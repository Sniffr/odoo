from odoo import models, fields, api
from datetime import datetime, timedelta


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
    
    service_id = fields.Many2one('company.service', string='Service', required=True)
    staff_member_id = fields.Many2one('custom.staff.member', string='Staff Member', required=True)
    branch_id = fields.Many2one('custom.branch', string='Branch')
    
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
    
    @api.model
    def create(self, vals):
        if not vals.get('name') and vals.get('service_id') and vals.get('customer_name'):
            service = self.env['company.service'].browse(vals['service_id'])
            vals['name'] = f"{service.name} - {vals['customer_name']}"
        
        if vals.get('staff_member_id'):
            staff = self.env['custom.staff.member'].browse(vals['staff_member_id'])
            if staff.employee_id and staff.employee_id.user_id:
                vals['user_id'] = staff.employee_id.user_id.id
        
        appointment = super(Appointment, self).create(vals)
        appointment._create_calendar_event()
        return appointment
    
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
        self.state = 'confirmed'
        return True
    
    def action_start(self):
        self.state = 'in_progress'
        return True
    
    def action_complete(self):
        self.state = 'completed'
        return True
    
    def action_cancel(self):
        self.state = 'cancelled'
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
