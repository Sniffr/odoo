from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
import base64
from icalendar import Calendar, Event as ICalEvent
import pytz
import logging

_logger = logging.getLogger(__name__)


class Appointment(models.Model):
    _name = 'custom.appointment'
    _description = 'Customer Appointment'
    _rec_name = 'name'
    _order = 'start desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Appointment Title', required=True)
    customer_name = fields.Char(string='Customer Name', required=True)
    customer_email = fields.Char(string='Customer Email', required=True)
    customer_phone = fields.Char(string='Customer Phone')
    partner_id = fields.Many2one('res.partner', string='Customer', ondelete='set null', 
                                 help='Customer partner record for CRM and payment tracking')
    
    service_id = fields.Many2one('company.service', string='Service', required=True, ondelete='cascade')
    staff_member_id = fields.Many2one('custom.staff.member', string='Staff Member', required=True, ondelete='cascade')
    branch_id = fields.Many2one('custom.branch', string='Branch', ondelete='set null')
    
    start = fields.Datetime(string='Start Time', required=True)
    stop = fields.Datetime(string='End Time', required=True)
    duration = fields.Float(string='Duration (Hours)', compute='_compute_duration', store=True)
    
    description = fields.Text(string='Description')
    
    calendar_event_id = fields.Many2one('calendar.event', string='Calendar Event')
    user_id = fields.Many2one('res.users', string='Responsible User')
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', required=True)
    
    price = fields.Monetary(string='Price', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='Currency', 
                                  default=lambda self: self.env.company.currency_id)
    
    internal_notes = fields.Text(string='Internal Notes')
    
    payment_status = fields.Selection([
        ('pending', 'Payment Pending'),
        ('paid', 'Paid'),
        ('failed', 'Payment Failed'),
        ('refunded', 'Refunded')
    ], string='Payment Status', default='pending', required=True)
    
    payment_transaction_id = fields.Many2one('payment.transaction', string='Payment Transaction')
    payment_method = fields.Char(string='Payment Method')
    payment_reference = fields.Char(string='Payment Reference')
    paid_amount = fields.Monetary(string='Paid Amount', currency_field='currency_id')
    payment_date = fields.Datetime(string='Payment Date')
    
    @api.depends('start', 'stop')
    def _compute_duration(self):
        for appointment in self:
            if appointment.start and appointment.stop:
                delta = appointment.stop - appointment.start
                appointment.duration = delta.total_seconds() / 3600.0
            else:
                appointment.duration = 0.0
    
    @api.onchange('service_id')
    def _onchange_service_id(self):
        if self.service_id:
            self.price = self.service_id.price
            self.currency_id = self.service_id.currency_id
            if self.start and self.service_id.duration:
                self.stop = self.start + timedelta(hours=self.service_id.duration)
    
    @api.onchange('staff_member_id')
    def _onchange_staff_member_id(self):
        if self.staff_member_id:
            self.branch_id = self.staff_member_id.branch_id
            if self.staff_member_id.employee_id and self.staff_member_id.employee_id.user_id:
                self.user_id = self.staff_member_id.employee_id.user_id
    
    @api.onchange('start', 'service_id')
    def _onchange_start_time(self):
        if self.start and self.service_id and self.service_id.duration:
            self.stop = self.start + timedelta(hours=self.service_id.duration)
    
    @api.constrains('staff_member_id', 'start', 'stop', 'state')
    def _check_staff_availability(self):
        """Validate that the staff member doesn't have overlapping appointments"""
        for appointment in self:
            # Skip validation for cancelled appointments
            if appointment.state == 'cancelled':
                continue
            
            if not appointment.start or not appointment.stop or not appointment.staff_member_id:
                continue
            
            # Search for conflicting appointments
            domain = [
                ('staff_member_id', '=', appointment.staff_member_id.id),
                ('id', '!=', appointment.id),  # Exclude current appointment
                ('state', 'in', ['draft', 'confirmed', 'in_progress']),  # Only active appointments
                ('start', '<', appointment.stop),
                ('stop', '>', appointment.start),
            ]
            
            conflicting_appointments = self.search(domain, limit=1)
            
            if conflicting_appointments:
                raise ValidationError(_(
                    'The staff member "%s" already has an appointment scheduled from %s to %s. '
                    'Please choose a different time slot or staff member.'
                ) % (
                    appointment.staff_member_id.name,
                    conflicting_appointments.start.strftime('%Y-%m-%d %H:%M'),
                    conflicting_appointments.stop.strftime('%Y-%m-%d %H:%M')
                ))
    
    def _find_or_create_partner(self, name, email, phone=None):
        """Find existing partner by email or create a new one"""
        Partner = self.env['res.partner'].sudo()
        
        partner = Partner.search([('email', '=', email)], limit=1)
        
        if partner:
            if phone and not partner.phone:
                partner.write({'phone': phone})
            return partner
        
        partner_vals = {
            'name': name,
            'email': email,
            'phone': phone,
            'customer_rank': 1,
            'is_company': False,
        }
        
        return Partner.create(partner_vals)
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') and vals.get('service_id') and vals.get('customer_name'):
                service = self.env['company.service'].browse(vals['service_id'])
                vals['name'] = f"{service.name} - {vals['customer_name']}"
            
            if vals.get('staff_member_id'):
                staff = self.env['custom.staff.member'].browse(vals['staff_member_id'])
                if staff.employee_id and staff.employee_id.user_id:
                    vals['user_id'] = staff.employee_id.user_id.id
            
            if not vals.get('partner_id') and vals.get('customer_email'):
                partner = self._find_or_create_partner(
                    vals.get('customer_name'),
                    vals.get('customer_email'),
                    vals.get('customer_phone')
                )
                vals['partner_id'] = partner.id
        
        appointments = super(Appointment, self).create(vals_list)
        appointments._create_calendar_event()
        return appointments
    
    def _create_calendar_event(self):
        """Create a corresponding calendar event for this appointment"""
        for appointment in self:
            if not appointment.calendar_event_id and appointment.start and appointment.stop:
                event_vals = {
                    'name': appointment.name,
                    'start': appointment.start,
                    'stop': appointment.stop,
                    'description': appointment.description or '',
                    'user_id': appointment.user_id.id if appointment.user_id else False,
                }
                calendar_event = self.env['calendar.event'].create(event_vals)
                appointment.calendar_event_id = calendar_event.id
    
    def write(self, vals):
        result = super(Appointment, self).write(vals)
        if any(field in vals for field in ['name', 'start', 'stop', 'description', 'user_id']):
            self._update_calendar_event()
        return result
    
    def _update_calendar_event(self):
        """Update the corresponding calendar event"""
        for appointment in self:
            if appointment.calendar_event_id:
                event_vals = {
                    'name': appointment.name,
                    'start': appointment.start,
                    'stop': appointment.stop,
                    'description': appointment.description or '',
                    'user_id': appointment.user_id.id if appointment.user_id else False,
                }
                appointment.calendar_event_id.write(event_vals)
    
    def action_confirm(self):
        if self.payment_status != 'paid':
            from odoo.exceptions import UserError
            raise UserError("Cannot confirm appointment without successful payment.")
        self.state = 'confirmed'
        self._send_confirmation_notifications()
        self._send_staff_notification()
        return True
    
    def action_start(self):
        self.state = 'in_progress'
        return True
    
    def action_complete(self):
        self.state = 'completed'
        return True
    
    def action_cancel(self):
        self.state = 'cancelled'
        self._send_cancellation_notifications()
        return True
    
    def action_reset_to_draft(self):
        self.state = 'draft'
        return True
    
    @api.model
    def get_my_appointments(self):
        """Get appointments for the current user"""
        if not self.env.user:
            return self.browse([])
        
        my_appointments = self.search([('user_id', '=', self.env.user.id)])
        
        staff_members = self.env['custom.staff.member'].search([
            ('employee_id.user_id', '=', self.env.user.id)
        ])
        if staff_members:
            staff_appointments = self.search([('staff_member_id', 'in', staff_members.ids)])
            my_appointments = my_appointments | staff_appointments
        
        return my_appointments
    
    def _generate_ics_attachment(self):
        """Generate .ics calendar invite file for the appointment"""
        self.ensure_one()
        import pytz
        
        cal = Calendar()
        cal.add('prodid', '-//Odoo Appointment System//EN')
        cal.add('version', '2.0')
        cal.add('method', 'REQUEST')
        
        try:
            local_tz = pytz.timezone(self.env.user.tz or 'Africa/Nairobi')
        except:
            local_tz = pytz.timezone('Africa/Nairobi')
        
        local_start = self._get_local_datetime(self.start)
        local_stop = self._get_local_datetime(self.stop)
        
        event = ICalEvent()
        event.add('summary', self.name)
        event.add('dtstart', local_start)
        event.add('dtend', local_stop)
        event.add('dtstamp', datetime.now(pytz.utc))
        
        location_parts = []
        if self.branch_id:
            if self.branch_id.name:
                location_parts.append(self.branch_id.name)
            if self.branch_id.street:
                location_parts.append(self.branch_id.street)
            if self.branch_id.city:
                location_parts.append(self.branch_id.city)
        
        if location_parts:
            event.add('location', ', '.join(location_parts))
        
        description_parts = [
            f"Service: {self.service_id.name}",
            f"Staff Member: {self.staff_member_id.name}",
            f"Duration: {self.duration} hours",
        ]
        
        if self.branch_id and self.branch_id.phone:
            description_parts.append(f"Contact: {self.branch_id.phone}")
        
        if self.description:
            description_parts.append(f"\nNotes: {self.description}")
        
        event.add('description', '\n'.join(description_parts))
        event.add('uid', f'appointment-{self.id}@{self.env.company.name.replace(" ", "-")}')
        event.add('priority', 5)
        event.add('sequence', 0)
        event.add('status', 'CONFIRMED')
        
        if self.customer_email:
            event.add('attendee', f'MAILTO:{self.customer_email}')
        
        if self.staff_member_id.email:
            event.add('organizer', f'MAILTO:{self.staff_member_id.email}')
        
        cal.add_component(event)
        
        ics_content = cal.to_ical()
        ics_base64 = base64.b64encode(ics_content)
        
        attachment = self.env['ir.attachment'].create({
            'name': f'appointment_{self.id}.ics',
            'datas': ics_base64,
            'res_model': 'custom.appointment',
            'res_id': self.id,
            'mimetype': 'text/calendar',
        })
        
        return attachment
    
    def _get_local_datetime(self, utc_datetime):
        """Convert UTC datetime to local timezone (EAT)"""
        import pytz
        from datetime import datetime
        
        if not utc_datetime:
            return None
        
        try:
            local_tz = pytz.timezone(self.env.user.tz or 'Africa/Nairobi')
        except:
            local_tz = pytz.timezone('Africa/Nairobi')
        
        if isinstance(utc_datetime, str):
            utc_datetime = datetime.strptime(utc_datetime, '%Y-%m-%d %H:%M:%S')
        
        if utc_datetime.tzinfo is None:
            utc_datetime = pytz.utc.localize(utc_datetime)
        
        return utc_datetime.astimezone(local_tz)
    
    def _load_email_template(self, template_name):
        """Load HTML email template from file"""
        import os
        module_path = os.path.dirname(os.path.dirname(__file__))
        template_path = os.path.join(module_path, 'templates', 'email', f'{template_name}.html')
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _generate_confirmation_email_html(self):
        """Generate HTML for confirmation email"""
        self.ensure_one()
        template = self._load_email_template('confirmation')
        
        return template.format(
            customer_name=self.customer_name,
            service_name=self.service_id.name,
            staff_name=self.staff_member_id.name,
            start_formatted=self.start.strftime('%A, %B %d, %Y - %I:%M %p'),
            duration=self.duration,
            branch_name=self.branch_id.name,
            price=self.price,
            currency_symbol=self.currency_id.symbol,
            branch_phone=self.branch_id.phone or self.env.user.company_id.phone,
            branch_email=self.branch_id.email or self.env.user.company_id.email,
            company_name=self.env.user.company_id.name,
            branch_address=f"{self.branch_id.street}, {self.branch_id.city}"
        )
    
    def _send_confirmation_notifications(self):
        """Send confirmation email to customer and SMS if phone is provided"""
        for appointment in self:
            if appointment.customer_email:
                _logger.info(f"Sending confirmation email to customer {appointment.customer_name} ({appointment.customer_email}) for appointment {appointment.id}")
                try:
                    ics_attachment = appointment._generate_ics_attachment()
                    _logger.info(f"Generated calendar invite attachment (ID: {ics_attachment.id}) for appointment {appointment.id}")
                    
                    subject = f"Appointment Confirmed - {appointment.name}"
                    body_html = appointment._generate_confirmation_email_html()
                    email_from = appointment.branch_id.email or self.env.user.company_id.email or 'noreply@localhost'
                    
                    mail = self.env['mail.mail'].sudo().create({
                        'subject': subject,
                        'body_html': body_html,
                        'email_to': appointment.customer_email,
                        'email_from': email_from,
                        'attachment_ids': [(4, ics_attachment.id)],
                    })
                    mail.send()
                    _logger.info(f"Successfully sent confirmation email with calendar invite to {appointment.customer_email}")
                except Exception as e:
                    _logger.error(f"Failed to send confirmation email to {appointment.customer_email}: {str(e)}", exc_info=True)
            
            if appointment.customer_phone:
                self._send_sms_notification(
                    appointment.customer_phone,
                    f"Appointment confirmed! {appointment.service_id.name} with {appointment.staff_member_id.name} on {appointment.start.strftime('%B %d at %I:%M %p')}. See you soon!"
                )
    
    def _generate_cancellation_email_html(self):
        """Generate HTML for cancellation email"""
        self.ensure_one()
        template = self._load_email_template('cancellation')
        
        return template.format(
            customer_name=self.customer_name,
            service_name=self.service_id.name,
            staff_name=self.staff_member_id.name,
            start_formatted=self.start.strftime('%A, %B %d, %Y - %I:%M %p'),
            branch_name=self.branch_id.name,
            branch_phone=self.branch_id.phone or self.env.user.company_id.phone,
            branch_email=self.branch_id.email or self.env.user.company_id.email,
            company_name=self.env.user.company_id.name,
            branch_address=f"{self.branch_id.street}, {self.branch_id.city}"
        )
    
    def _send_cancellation_notifications(self):
        """Send cancellation email to customer and SMS if phone is provided"""
        for appointment in self:
            if appointment.customer_email:
                _logger.info(f"Sending cancellation email to customer {appointment.customer_name} ({appointment.customer_email}) for appointment {appointment.id}")
                try:
                    subject = f"Appointment Cancelled - {appointment.name}"
                    body_html = appointment._generate_cancellation_email_html()
                    email_from = appointment.branch_id.email or self.env.user.company_id.email or 'noreply@localhost'
                    
                    mail = self.env['mail.mail'].sudo().create({
                        'subject': subject,
                        'body_html': body_html,
                        'email_to': appointment.customer_email,
                        'email_from': email_from,
                    })
                    mail.send()
                    _logger.info(f"Successfully sent cancellation email to {appointment.customer_email}")
                except Exception as e:
                    _logger.error(f"Failed to send cancellation email to {appointment.customer_email}: {str(e)}", exc_info=True)
            
            if appointment.customer_phone:
                self._send_sms_notification(
                    appointment.customer_phone,
                    f"Your appointment for {appointment.service_id.name} on {appointment.start.strftime('%B %d at %I:%M %p')} has been cancelled. Please contact us to reschedule."
                )
    
    def _generate_staff_notification_email_html(self):
        """Generate HTML for staff notification email"""
        self.ensure_one()
        template = self._load_email_template('staff_notification')
        
        return template.format(
            staff_name=self.staff_member_id.name,
            customer_name=self.customer_name,
            customer_email=self.customer_email,
            customer_phone=self.customer_phone or 'Not provided',
            service_name=self.service_id.name,
            start_formatted=self.start.strftime('%A, %B %d, %Y - %I:%M %p'),
            duration=self.duration,
            branch_name=self.branch_id.name,
            company_name=self.env.user.company_id.name,
            branch_address=f"{self.branch_id.street}, {self.branch_id.city}"
        )
    
    def _send_staff_notification(self):
        """Send notification to staff member about new appointment"""
        for appointment in self:
            if appointment.staff_member_id.email:
                _logger.info(f"Sending notification email to staff {appointment.staff_member_id.name} ({appointment.staff_member_id.email}) for appointment {appointment.id}")
                try:
                    ics_attachment = appointment._generate_ics_attachment()
                    _logger.info(f"Generated calendar invite attachment (ID: {ics_attachment.id}, name: {ics_attachment.name}, mimetype: {ics_attachment.mimetype}) for staff notification")
                    
                    subject = f"New Appointment Booked - {appointment.name}"
                    body_html = appointment._generate_staff_notification_email_html()
                    email_from = self.env.user.company_id.email or 'noreply@localhost'
                    
                    mail = self.env['mail.mail'].sudo().create({
                        'subject': subject,
                        'body_html': body_html,
                        'email_to': appointment.staff_member_id.email,
                        'email_from': email_from,
                        'attachment_ids': [(4, ics_attachment.id)],
                    })
                    _logger.info(f"Created mail record (ID: {mail.id}) with attachment IDs: {mail.attachment_ids.ids}")
                    mail.send()
                    _logger.info(f"Successfully sent staff notification email with calendar invite to {appointment.staff_member_id.email}")
                except Exception as e:
                    _logger.error(f"Failed to send staff notification to {appointment.staff_member_id.email}: {str(e)}", exc_info=True)
    
    def _generate_reminder_email_html(self):
        """Generate HTML for reminder email"""
        self.ensure_one()
        template = self._load_email_template('reminder')
        
        return template.format(
            customer_name=self.customer_name,
            service_name=self.service_id.name,
            staff_name=self.staff_member_id.name,
            start_formatted=self.start.strftime('%A, %B %d, %Y - %I:%M %p'),
            duration=self.duration,
            branch_name=self.branch_id.name,
            branch_phone=self.branch_id.phone or self.env.user.company_id.phone,
            branch_email=self.branch_id.email or self.env.user.company_id.email,
            company_name=self.env.user.company_id.name,
            branch_address=f"{self.branch_id.street}, {self.branch_id.city}"
        )
    
    def _send_reminder_notifications(self):
        """Send reminder notifications (to be called by scheduled action)"""
        for appointment in self:
            if appointment.customer_email:
                subject = f"Reminder: Your appointment tomorrow - {appointment.name}"
                body_html = appointment._generate_reminder_email_html()
                email_from = appointment.branch_id.email or self.env.user.company_id.email or 'noreply@localhost'
                
                mail = self.env['mail.mail'].sudo().create({
                    'subject': subject,
                    'body_html': body_html,
                    'email_to': appointment.customer_email,
                    'email_from': email_from,
                })
                mail.send()
            
            if appointment.customer_phone:
                self._send_sms_notification(
                    appointment.customer_phone,
                    f"Reminder: Your appointment for {appointment.service_id.name} is tomorrow at {appointment.start.strftime('%I:%M %p')} with {appointment.staff_member_id.name}."
                )
    
    def _send_sms_notification(self, phone_number, message):
        """Send SMS notification using Odoo's SMS gateway"""
        try:
            self.env['sms.sms'].create({
                'number': phone_number,
                'body': message,
                'state': 'outgoing',
            })
        except Exception as e:
            import logging
            _logger = logging.getLogger(__name__)
            _logger.warning(f"Failed to send SMS to {phone_number}: {str(e)}")
    
    @api.model
    def send_appointment_reminders(self):
        """Scheduled method to send appointment reminders 24 hours before"""
        from datetime import datetime, timedelta
        
        tomorrow = datetime.now() + timedelta(days=1)
        start_of_day = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = tomorrow.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        appointments = self.search([
            ('state', '=', 'confirmed'),
            ('start', '>=', start_of_day),
            ('start', '<=', end_of_day)
        ])
        
        for appointment in appointments:
            appointment._send_reminder_notifications()
