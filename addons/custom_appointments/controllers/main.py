from odoo import http
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
        salon_id = kwargs.get('salon_id')
        
        services = request.env['company.service'].sudo().get_available_services()
        service_categories = request.env['service.category'].sudo().search([
            ('active', '=', True)
        ], order='sequence, name')
        
        staff_members = request.env['custom.staff.member'].sudo().search([
            ('is_bookable', '=', True),
            ('active', '=', True)
        ], order='name')
        
        selected_branch = None
        if salon_id:
            selected_branch = request.env['res.company'].sudo().browse(int(salon_id))
        
        return request.render('custom_appointments.service_selection_page', {
            'services': services,
            'service_categories': service_categories,
            'staff_members': staff_members,
            'selected_staff_id': staff_id,
            'selected_branch': selected_branch,
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
            
            appointment = request.env['custom.appointment'].sudo().create(appointment_vals)
            
            return request.render('custom_appointments.booking_success_page', {
                'appointment': appointment,
                'service': service,
                'staff': staff,
            })
            
        except Exception as e:
            return request.render('custom_appointments.booking_error_page', {
                'error': str(e),
            })
