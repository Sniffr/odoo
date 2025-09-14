from odoo import models, fields, api


class ServiceCategory(models.Model):
    _name = 'service.category'
    _description = 'Service Category'
    _rec_name = 'name'

    name = fields.Char(string='Category Name', required=True)
    code = fields.Char(string='Category Code')
    description = fields.Text(string='Description')
    image = fields.Image(string='Category Image', help='Image representing this category')
    color = fields.Integer(string='Color', help='Color for display purposes')
    
    service_ids = fields.One2many('company.service', 'category_id', string='Services')
    service_count = fields.Integer(string='Service Count', compute='_compute_service_count')
    
    active = fields.Boolean(string='Active', default=True)
    sequence = fields.Integer(string='Sequence', default=10)
    
    @api.depends('service_ids')
    def _compute_service_count(self):
        for record in self:
            record.service_count = len(record.service_ids)
    
    def action_view_services(self):
        """Action to view services for this category"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Services',
            'res_model': 'company.service',
            'view_mode': 'list,form',
            'domain': [('category_id', '=', self.id)],
            'context': {'default_category_id': self.id},
        }
