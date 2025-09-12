from odoo import http
from odoo.http import request


class ServicesController(http.Controller):

    @http.route('/services', type='http', auth='public', website=True)
    def service_list(self, category_id=None, **kwargs):
        """Display list of available services"""
        domain = [
            ('active', '=', True),
            ('website_published', '=', True)
        ]
        
        if category_id:
            domain.append(('category_id', '=', int(category_id)))
        
        services = request.env['company.service'].sudo().search(domain, order='sequence, name')
        categories = request.env['service.category'].sudo().search([('active', '=', True)], order='sequence, name')
        
        return request.render('services.service_list_template', {
            'services': services,
            'categories': categories,
            'current_category': int(category_id) if category_id else None,
        })

    @http.route('/services/<int:service_id>', type='http', auth='public', website=True)
    def service_detail(self, service_id, **kwargs):
        """Display service details"""
        service = request.env['company.service'].sudo().browse(service_id)
        
        if not service.exists() or not service.active or not service.website_published:
            return request.not_found()
        
        return request.render('services.service_detail_template', {
            'service': service,
        })
