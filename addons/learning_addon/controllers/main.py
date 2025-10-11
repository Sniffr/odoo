from odoo import http
from odoo.http import request


class LearningController(http.Controller):

    @http.route('/learning', type='http', auth='public', website=True)
    def learning_records(self, **kwargs):
        """Display all learning records on the website"""
        records = request.env['learning.record'].sudo().search([])
        return request.render('learning_addon.learning_records_template', {
            'records': records,
        })

    @http.route('/learning/<int:record_id>', type='http', auth='public', website=True)
    def learning_record_detail(self, record_id, **kwargs):
        """Display a single learning record detail"""
        record = request.env['learning.record'].sudo().browse(record_id)
        if not record.exists():
            return request.not_found()
        
        return request.render('learning_addon.learning_record_detail_template', {
            'record': record,
        })
