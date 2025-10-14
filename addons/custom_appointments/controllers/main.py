from odoo import http, fields
from odoo.http import request
from datetime import datetime, timedelta
import json


class AppointmentController(http.Controller):

    @http.route('/appointments', type='http', auth='public', website=True)
    def appointment_booking(self, **kwargs):
        """Main appointment booking page - Location and staff selection"""
        staff_members = request.env['custom.staff.member'].sudo().search([
            ('is_bookable', '=', True),
            ('active', '=', True)
        ], order='name')
        
        branches = request.env['res.company'].sudo().search([
            ('active', '=', True)
        ], order='name')
        
        return request.render('custom_appointments.appointment_booking_page', {
            'staff_members': staff_members,
            'branches': branches,
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
        
        staff_members = request.env['custom.staff.member'].sudo().search([
            ('is_bookable', '=', True),
            ('active', '=', True)
        ], order='name')
        
        selected_branch = None
        selected_staff = None

        # Get selected branch details if branch_id provided
        if branch_id:
            selected_branch = request.env['res.company'].sudo().browse(int(branch_id))

        # Get selected staff details if staff_id provided
        if staff_id and staff_id != 'any':
            selected_staff = request.env['custom.staff.member'].sudo().browse(int(staff_id))

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
            
            return request.render('custom_appointments.booking_form_page', {
                'service': service,
                'staff': staff,
                'available_slots': available_slots,
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
        """Get available time slots for a specific date"""
        weekday = date.weekday()  # 0=Monday, 6=Sunday
        day_fields = [
            'monday_available', 'tuesday_available', 'wednesday_available',
            'thursday_available', 'friday_available', 'saturday_available', 'sunday_available'
        ]
        
        if not getattr(staff, day_fields[weekday]):
            return []
        
        start_hour = staff.start_time
        end_hour = staff.end_time
        service_duration = service.duration
        
        slots = []
        current_time = start_hour
        
        while current_time + service_duration <= end_hour:
            slot_datetime = datetime.combine(date, datetime.min.time()) + timedelta(hours=current_time)
            
            if not self._has_conflict(staff, slot_datetime, service_duration):
                slots.append({
                    'time': slot_datetime.strftime('%H:%M'),
                    'datetime': slot_datetime.isoformat(),
                })
            
            current_time += 0.5
        
        return slots

    def _has_conflict(self, staff, start_datetime, duration_hours):
        """Check if a time slot conflicts with existing appointments"""
        end_datetime = start_datetime + timedelta(hours=duration_hours)
        
        existing_appointments = request.env['custom.appointment'].sudo().search([
            ('staff_member_id', '=', staff.id),
            ('state', 'in', ['confirmed', 'in_progress']),
            ('start', '<', end_datetime),
            ('stop', '>', start_datetime),
        ])
        
        return len(existing_appointments) > 0

    def _process_booking(self, data):
        """Process the booking form submission"""
        try:
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
            
            start_dt = datetime.fromisoformat(appointment_datetime.replace('Z', '+00:00'))
            end_dt = start_dt + timedelta(hours=service.duration)
            
            if self._has_conflict(staff, start_dt, service.duration):
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
            return request.render('custom_appointments.booking_error_page', {
                'error': str(e),
            })
    
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
            
            return request.render('custom_appointments.payment_page', {
                'appointment': appointment,
                'acquirers': acquirers,
                'amount': appointment.price,
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
            
            transaction_vals = {
                'amount': appointment.price,
                'currency_id': appointment.currency_id.id,
                'provider_id': acquirer.id,
                'reference': f"APPT-{appointment.id}-{appointment.customer_name}",
                'partner_id': request.env.user.partner_id.id if request.env.user != request.env.ref('base.public_user') else False,
                'partner_name': appointment.customer_name,
                'partner_email': appointment.customer_email,
            }
            
            transaction = request.env['payment.transaction'].sudo().create(transaction_vals)
            appointment.payment_transaction_id = transaction.id
            
            return request.redirect(transaction.get_portal_url())
            
        except Exception as e:
            return request.render('custom_appointments.payment_error_page', {
                'error': str(e),
            })
    
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
                        'state': 'confirmed'
                    })
                    appointment._send_confirmation_notifications()
                elif transaction.state in ['cancel', 'error']:
                    appointment.write({
                        'payment_status': 'failed'
                    })
            
            return request.make_response('OK', status=200)
            
        except Exception as e:
            return request.make_response(f'Error: {str(e)}', status=500)
    
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
