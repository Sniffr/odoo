from odoo import http
from odoo.http import request


class CustomAppointmentsController(http.Controller):

    @http.route('/appointments/staff', type='http', auth='public', website=True)
    def staff_list(self, **kwargs):
        """Display list of available staff members"""
        staff_members = request.env['custom.staff.member'].sudo().search([
            ('is_bookable', '=', True),
            ('active', '=', True)
        ])
        
        return request.render('custom_appointments.staff_list_template', {
            'staff_members': staff_members,
        })

    @http.route('/appointments/branches', type='http', auth='public', website=True)
    def branch_list(self, **kwargs):
        """Display list of company branches"""
        branches = request.env['custom.branch'].sudo().search([
            ('active', '=', True)
        ])
        
        return request.render('custom_appointments.branch_list_template', {
            'branches': branches,
        })
