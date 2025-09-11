from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

class AppointmentsController(http.Controller):
    
    @http.route('/appointments/staff', type='http', auth='public', website=True, sitemap=True)
    def staff_list(self, **kwargs):
        staff_members = request.env['res.partner'].sudo().search([
            ('is_bookable', '=', True)
        ])
        
        values = {
            'staff_members': staff_members,
        }
        
        return request.render('appointments.staff_list_template', values)
    
    @http.route('/appointments/staff/<int:staff_id>', type='http', auth='public', website=True, sitemap=True)
    def staff_profile(self, staff_id, **kwargs):
        staff_member = request.env['res.partner'].sudo().browse(staff_id)
        
        if not staff_member.exists() or not staff_member.is_bookable:
            return request.render('website.404')
        
        values = {
            'staff_member': staff_member,
        }
        
        return request.render('appointments.staff_profile_template', values)
