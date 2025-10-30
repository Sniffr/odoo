from odoo import http, fields
from odoo.http import request
from werkzeug.utils import redirect
from datetime import datetime, timedelta
import json


class AppointmentController(http.Controller):

    @http.route('/appointments', type='http', auth='public', website=True)
    def appointment_booking(self, **kwargs):
        """Main appointment booking page - Location and staff selection"""
        branch_id = kwargs.get('branch_id')
        
        branches = request.env['custom.branch'].sudo().search([
            ('active', '=', True)
        ], order='name')
        
        selected_branch = None
        if branch_id:
            selected_branch = request.env['custom.branch'].sudo().browse(int(branch_id))
        elif branches:
            main_branch = request.env['custom.branch'].sudo().search([
                ('is_main_branch', '=', True),
                ('active', '=', True)
            ], limit=1)
            selected_branch = main_branch if main_branch else branches[0]
        
        staff_domain = [
            ('is_bookable', '=', True),
            ('active', '=', True)
        ]
        if selected_branch:
            staff_domain.append(('branch_id', '=', selected_branch.id))
        
        staff_members = request.env['custom.staff.member'].sudo().search(staff_domain, order='name')
        
        return request.render('custom_appointments.appointment_booking_page', {
            'staff_members': staff_members,
            'branches': branches,
            'selected_branch': selected_branch,
        })

    @http.route('/appointments/services', type='http', auth='public', website=True)
    def service_selection(self, **kwargs):
        """Professional service selection page"""
        staff_id = kwargs.get('staff_id')
        branch_id = kwargs.get('branch_id')

        services = request.env['company.service'].sudo().get_available_services()
        service_categories = request.env['service.category'].sudo().search([
            ('active', '=', True)
        ], order='sequence, name')
        
        selected_branch = None
        selected_staff = None

        if staff_id and staff_id != 'any':
            selected_staff = request.env['custom.staff.member'].sudo().browse(int(staff_id))
            if selected_staff.exists() and selected_staff.branch_id:
                selected_branch = selected_staff.branch_id

        if branch_id:
            selected_branch = request.env['custom.branch'].sudo().browse(int(branch_id))

        staff_domain = [
            ('is_bookable', '=', True),
            ('active', '=', True)
        ]
        if branch_id:
            staff_domain.append(('branch_id', '=', int(branch_id)))
        elif selected_branch:
            staff_domain.append(('branch_id', '=', selected_branch.id))
        
        staff_members = request.env['custom.staff.member'].sudo().search(staff_domain, order='name')

        return request.render('custom_appointments.service_selection_page', {
            'services': services,
            'service_categories': service_categories,
            'staff_members': staff_members,
            'selected_staff_id': staff_id,
            'selected_branch': selected_branch,
            'selected_staff': selected_staff,
        })

    @http.route('/appointments/book', type='http', auth='public', website=True, methods=['GET', 'POST'])
    def book_appointment(self, **kwargs):
        """Appointment booking form"""
        if request.httprequest.method == 'GET':
            service_id = kwargs.get('service_id')
            staff_id = kwargs.get('staff_id')
            
            if not service_id or not staff_id:
                return request.redirect('/appointments')
            
            service = request.env['company.service'].sudo().browse(int(service_id))
            staff = request.env['custom.staff.member'].sudo().browse(int(staff_id))
            
            if not service.exists() or not staff.exists():
                return request.redirect('/appointments')
            
            available_slots = self._get_available_slots(service, staff)
            
            import json
            available_slots_json = json.dumps(available_slots)
            
            return request.render('custom_appointments.booking_form_page', {
                'service': service,
                'staff': staff,
                'available_slots': available_slots,
                'available_slots_json': available_slots_json,
            })
        
        elif request.httprequest.method == 'POST':
            return self._process_booking(kwargs)

    @http.route('/appointments/slots', type='json', auth='public', website=True)
    def get_available_slots(self, service_id, staff_id, date=None):
        """AJAX endpoint to get available time slots for a specific date"""
        service = request.env['company.service'].sudo().browse(service_id)
        staff = request.env['custom.staff.member'].sudo().browse(staff_id)
        
        if not service.exists() or not staff.exists():
            return {'error': 'Invalid service or staff'}
        
        if date:
            target_date = datetime.strptime(date, '%Y-%m-%d').date()
        else:
            target_date = datetime.now().date()
        
        slots = self._get_slots_for_date(service, staff, target_date)
        return {'slots': slots}

    def _get_available_slots(self, service, staff, days_ahead=30):
        """Get available time slots for the next N days"""
        slots_by_date = {}
        today = datetime.now().date()
        
        for i in range(days_ahead):
            date = today + timedelta(days=i)
            slots = self._get_slots_for_date(service, staff, date)
            if slots:
                slots_by_date[date.strftime('%Y-%m-%d')] = slots
        
        return slots_by_date

    def _get_slots_for_date(self, service, staff, date):
        """Get available time slots for a specific date based on staff availability and service duration"""
        import pytz
        
        weekday = date.weekday()
        day_fields = [
            'monday_available', 'tuesday_available', 'wednesday_available',
            'thursday_available', 'friday_available', 'saturday_available', 'sunday_available'
        ]
        
        if not getattr(staff, day_fields[weekday]):
            return []
        
        start_hour = staff.start_time
        end_hour = staff.end_time
        service_duration = service.duration
        
        tz_name = request.env['ir.config_parameter'].sudo().get_param('appointment.timezone', 'Africa/Nairobi')
        try:
            server_tz = pytz.timezone(tz_name)
        except:
            server_tz = pytz.timezone('Africa/Nairobi')
        
        now_server = datetime.now(server_tz)
        is_today = date == now_server.date()
        
        slots = []
        current_time = start_hour
        
        while current_time + service_duration <= end_hour:
            slot_datetime_naive = datetime.combine(date, datetime.min.time()) + timedelta(hours=current_time)
            
            if is_today and slot_datetime_naive <= now_server.replace(tzinfo=None):
                current_time += service_duration
                continue
            
            slot_datetime_local = server_tz.localize(slot_datetime_naive)
            slot_datetime_utc = slot_datetime_local.astimezone(pytz.utc).replace(tzinfo=None)
            
            if not self._has_conflict(staff, slot_datetime_utc, service_duration, service):
                slots.append({
                    'time': slot_datetime_naive.strftime('%H:%M'),
                    'datetime': slot_datetime_naive.isoformat(),
                    'display_time': slot_datetime_naive.strftime('%I:%M %p'),
                })
            
            current_time += service_duration
        
        return slots

    def _has_conflict(self, staff, start_datetime, duration_hours, service=None):
        """Check if a time slot conflicts with existing appointments including buffer time"""
        end_datetime = start_datetime + timedelta(hours=duration_hours)
        
        buffer_before = 0
        buffer_after = 0
        if service:
            buffer_before = service.preparation_time if hasattr(service, 'preparation_time') else 0
            buffer_after = service.cleanup_time if hasattr(service, 'cleanup_time') else 0
        
        check_start = start_datetime - timedelta(hours=buffer_before)
        check_end = end_datetime + timedelta(hours=buffer_after)
        
        existing_appointments = request.env['custom.appointment'].sudo().search([
            ('staff_member_id', '=', staff.id),
            ('state', 'in', ['draft', 'confirmed', 'in_progress']),
            ('start', '<', check_end),
            ('stop', '>', check_start),
        ])
        
        return len(existing_appointments) > 0

    def _process_booking(self, data):
        """Process the booking form submission"""
        try:
            import pytz
            
            service_id = int(data.get('service_id'))
            staff_id = int(data.get('staff_id'))
            appointment_datetime = data.get('appointment_datetime')
            customer_name = data.get('customer_name')
            customer_email = data.get('customer_email')
            customer_phone = data.get('customer_phone', '')
            notes = data.get('notes', '')
            
            service = request.env['company.service'].sudo().browse(service_id)
            staff = request.env['custom.staff.member'].sudo().browse(staff_id)
            
            if not service.exists() or not staff.exists():
                raise ValueError("Invalid service or staff")
            
            tz_name = request.env['ir.config_parameter'].sudo().get_param('appointment.timezone', 'Africa/Nairobi')
            try:
                server_tz = pytz.timezone(tz_name)
            except:
                server_tz = pytz.timezone('Africa/Nairobi')
            
            naive_dt = datetime.fromisoformat(appointment_datetime.replace('Z', '').replace('+00:00', ''))
            local_dt = server_tz.localize(naive_dt)
            start_dt = local_dt.astimezone(pytz.utc).replace(tzinfo=None)
            end_dt = start_dt + timedelta(hours=service.duration)
            
            if self._has_conflict(staff, start_dt, service.duration, service):
                raise ValueError("Time slot is no longer available")
            
            appointment_vals = {
                'name': f"{service.name} - {customer_name}",
                'customer_name': customer_name,
                'customer_email': customer_email,
                'customer_phone': customer_phone,
                'service_id': service.id,
                'staff_member_id': staff.id,
                'branch_id': staff.branch_id.id,
                'start': start_dt,
                'stop': end_dt,
                'description': notes,
                'price': service.price,
                'state': 'confirmed' if not service.requires_approval else 'draft',
            }
            
            appointment_vals['state'] = 'draft'
            appointment_vals['payment_status'] = 'pending'
            appointment = request.env['custom.appointment'].sudo().create(appointment_vals)
            
            return request.redirect(f'/appointments/payment?appointment_id={appointment.id}')
            
        except Exception as e:
            return request.redirect(f'/appointments?error={str(e)}')
    
    @http.route('/appointments/payment', type='http', auth='public', website=True, methods=['GET', 'POST'])
    def payment_page(self, **kwargs):
        """Payment page for appointment booking"""
        if request.httprequest.method == 'GET':
            appointment_id = kwargs.get('appointment_id')
            if not appointment_id:
                return request.redirect('/appointments')
            
            appointment = request.env['custom.appointment'].sudo().browse(int(appointment_id))
            if not appointment.exists() or appointment.payment_status == 'paid':
                return request.redirect('/appointments')
            
            acquirers = request.env['payment.provider'].sudo().search([
                ('state', 'in', ['enabled', 'test']),
                ('is_published', '=', True)
            ])
            
            amount_to_charge = appointment.service_id.get_amount_to_charge()
            
            return request.render('custom_appointments.payment_page', {
                'appointment': appointment,
                'acquirers': acquirers,
                'amount': amount_to_charge,
                'currency': appointment.currency_id,
            })
        
        elif request.httprequest.method == 'POST':
            return self._process_payment(kwargs)
    
    def _process_payment(self, data):
        """Process payment transaction"""
        try:
            appointment_id = int(data.get('appointment_id'))
            acquirer_id = int(data.get('acquirer_id'))
            
            appointment = request.env['custom.appointment'].sudo().browse(appointment_id)
            acquirer = request.env['payment.provider'].sudo().browse(acquirer_id)
            
            if not appointment.exists() or not acquirer.exists():
                raise ValueError("Invalid appointment or payment method")
            
            payment_method = request.env['payment.method'].sudo().search([
                ('code', '=', acquirer.code if acquirer.code != 'none' else 'card')
            ], limit=1)
            
            if not payment_method:
                payment_method = request.env['payment.method'].sudo().search([
                    ('code', '=', 'card')
                ], limit=1)
            
            if not payment_method:
                payment_method = request.env['payment.method'].sudo().search([], limit=1)
            
            if not payment_method:
                raise ValueError("No payment method available. Please contact support.")
            
            payment_method_line = request.env['account.payment.method.line'].sudo().search([
                ('payment_provider_id', '=', acquirer.id),
                ('payment_method_id', '=', payment_method.id),
            ], limit=1)
            
            if not payment_method_line:
                payment_method_line = request.env['account.payment.method.line'].sudo().search([
                    ('payment_method_id', '=', payment_method.id),
                    ('payment_type', '=', 'inbound'),
                ], limit=1)
            
            import time
            unique_ref = f"APPT-{appointment.id}-{int(time.time())}"
            
            amount_to_charge = appointment.service_id.get_amount_to_charge()
            
            if not appointment.partner_id:
                partner = appointment._find_or_create_partner(
                    appointment.customer_name,
                    appointment.customer_email,
                    appointment.customer_phone
                )
                appointment.partner_id = partner.id
            
            transaction_vals = {
                'amount': amount_to_charge,
                'currency_id': appointment.currency_id.id,
                'provider_id': acquirer.id,
                'payment_method_id': payment_method.id,
                'reference': unique_ref,
                'partner_id': appointment.partner_id.id,
                'partner_name': appointment.customer_name,
                'partner_email': appointment.customer_email,
            }
            
            if payment_method_line:
                transaction_vals['payment_method_line_id'] = payment_method_line.id
            
            transaction = request.env['payment.transaction'].sudo().create(transaction_vals)
            appointment.payment_transaction_id = transaction.id
            
            if acquirer.code == 'demo':
                transaction.write({'state': 'done'})
                appointment.write({
                    'payment_status': 'paid',
                    'paid_amount': transaction.amount,
                    'payment_date': fields.Datetime.now(),
                    'payment_method': acquirer.name,
                    'payment_reference': transaction.reference,
                })
                appointment.action_confirm()
                return request.redirect(f'/appointments/payment/success?appointment_id={appointment.id}')
            
            elif acquirer.code == 'mpesa':
                phone_number = data.get('mpesa_phone', '').strip()
                if not phone_number:
                    return request.redirect(f'/appointments/payment?appointment_id={appointment.id}&error=Phone number is required for M-Pesa payment')
                
                result = transaction._mpesa_initiate_stk_push(phone_number)
                if result:
                    return request.redirect(f'/appointments/payment/pending?appointment_id={appointment.id}')
                else:
                    return request.redirect(f'/appointments/payment?appointment_id={appointment.id}&error=Failed to initiate M-Pesa payment. Please try again.')
            
            elif acquirer.code == 'pesapal':
                processing_values = {
                    'reference': transaction.reference,
                    'amount': transaction.amount,
                    'currency': transaction.currency_id,
                    'partner_id': transaction.partner_id.id if transaction.partner_id else False,
                }
                
                try:
                    rendering_values = transaction._get_specific_rendering_values(processing_values)
                    redirect_url = rendering_values.get('redirect_url')
                    
                    if redirect_url:
                        return redirect(redirect_url, code=303)
                    else:
                        return request.redirect(f'/appointments/payment?appointment_id={appointment.id}&error=Failed to initialize PesaPal payment. Please try again.')
                except Exception as e:
                    error_msg = str(e).replace('\n', ' ').replace('\r', ' ')
                    return request.redirect(f'/appointments/payment?appointment_id={appointment.id}&error=PesaPal Error: {error_msg}')
            
            return request.redirect(f'/appointments/payment?appointment_id={appointment.id}&error=Payment method not yet fully configured')
            
        except Exception as e:
            error_msg = str(e).replace('\n', ' ').replace('\r', ' ')
            return request.redirect(f'/appointments/payment?appointment_id={appointment_id}&error={error_msg}')
    
    @http.route('/appointments/payment/webhook', type='http', auth='public', methods=['POST'], csrf=False)
    def payment_webhook(self, **kwargs):
        """Handle payment transaction status updates"""
        try:
            transaction_id = kwargs.get('transaction_id')
            if not transaction_id:
                return request.make_response('Missing transaction ID', status=400)
            
            transaction = request.env['payment.transaction'].sudo().browse(int(transaction_id))
            if not transaction.exists():
                return request.make_response('Transaction not found', status=404)
            
            appointment = request.env['custom.appointment'].sudo().search([
                ('payment_transaction_id', '=', transaction.id)
            ], limit=1)
            
            if appointment:
                if transaction.state == 'done':
                    appointment.write({
                        'payment_status': 'paid',
                        'paid_amount': transaction.amount,
                        'payment_date': fields.Datetime.now(),
                        'payment_method': transaction.provider_id.name,
                        'payment_reference': transaction.reference,
                    })
                    appointment.action_confirm()
                elif transaction.state in ['cancel', 'error']:
                    appointment.write({
                        'payment_status': 'failed'
                    })
            
            return request.make_response('OK', status=200)
            
        except Exception as e:
            return request.make_response(f'Error: {str(e)}', status=500)
    
    @http.route('/appointment/payment/status', type='json', auth='public')
    def check_payment_status(self, **kwargs):
        """Check payment status for appointment"""
        try:
            appointment_id = kwargs.get('appointment_id')
            if not appointment_id:
                return {'error': 'Missing appointment ID'}
            
            appointment = request.env['custom.appointment'].sudo().browse(int(appointment_id))
            if not appointment.exists():
                return {'error': 'Appointment not found'}
            
            return {
                'payment_status': appointment.payment_status,
                'state': appointment.state,
            }
        except Exception as e:
            return {'error': str(e)}
    
    @http.route('/appointments/payment/pending', type='http', auth='public', website=True)
    def payment_pending(self, **kwargs):
        """Payment pending page for M-Pesa"""
        appointment_id = kwargs.get('appointment_id')
        if not appointment_id:
            return request.redirect('/appointments')
        
        appointment = request.env['custom.appointment'].sudo().browse(int(appointment_id))
        if not appointment.exists():
            return request.redirect('/appointments')
        
        return request.render('custom_appointments.payment_pending_page', {
            'appointment': appointment,
        })
    
    @http.route('/appointments/payment/success', type='http', auth='public', website=True)
    def payment_success(self, **kwargs):
        """Payment success page"""
        appointment_id = kwargs.get('appointment_id')
        if not appointment_id:
            return request.redirect('/appointments')
        
        appointment = request.env['custom.appointment'].sudo().browse(int(appointment_id))
        if not appointment.exists():
            return request.redirect('/appointments')
        
        return request.render('custom_appointments.payment_success_page', {
            'appointment': appointment,
        })
