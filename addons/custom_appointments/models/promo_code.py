from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
import secrets
import string


class PromoCode(models.Model):
    _name = 'custom.appointment.promo'
    _description = 'Appointment Promo Code'
    _rec_name = 'code'
    _order = 'create_date desc'

    name = fields.Char(string='Promo Name', required=True, help='Internal name for this promotion')
    code = fields.Char(string='Promo Code', required=True, index=True, help='The code customers will enter')
    
    discount_type = fields.Selection([
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ], string='Discount Type', required=True, default='percentage')
    
    discount_value = fields.Float(string='Discount Value', required=True, 
                                   help='Percentage (0-100) or fixed amount depending on discount type')
    
    valid_from = fields.Date(string='Valid From', default=fields.Date.today)
    valid_to = fields.Date(string='Valid To')
    
    max_uses = fields.Integer(string='Maximum Uses', default=0, 
                               help='Maximum number of times this code can be used. 0 = unlimited')
    current_uses = fields.Integer(string='Current Uses', default=0, readonly=True)
    max_uses_per_customer = fields.Integer(string='Max Uses Per Customer', default=1,
                                            help='Maximum times a single customer can use this code. 0 = unlimited')
    
    assigned_staff_id = fields.Many2one('custom.staff.member', string='Assigned Staff/Affiliate',
                                         help='External staff or affiliate who owns this promo code for tracking')
    assigned_partner_id = fields.Many2one('res.partner', string='Assigned Partner',
                                           help='Partner/affiliate who owns this promo code')
    
    branch_ids = fields.Many2many('custom.branch', string='Valid Branches',
                                   help='Leave empty for all branches')
    service_ids = fields.Many2many('company.service', string='Valid Services',
                                    help='Leave empty for all services')
    
    active = fields.Boolean(string='Active', default=True)
    
    minimum_amount = fields.Float(string='Minimum Order Amount', default=0,
                                   help='Minimum appointment price to apply this promo')
    maximum_discount = fields.Float(string='Maximum Discount Amount', default=0,
                                     help='Cap on discount amount (for percentage discounts). 0 = no cap')
    
    appointment_ids = fields.One2many('custom.appointment', 'promo_id', string='Appointments')
    appointment_count = fields.Integer(string='Appointments', compute='_compute_appointment_count')
    
    total_discount_given = fields.Float(string='Total Discount Given', compute='_compute_stats', store=True)
    total_revenue = fields.Float(string='Total Revenue Generated', compute='_compute_stats', store=True)
    
    shareable_link = fields.Char(string='Shareable Link', compute='_compute_shareable_link')
    
    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Promo code must be unique!'),
    ]
    
    @api.depends('appointment_ids')
    def _compute_appointment_count(self):
        for promo in self:
            promo.appointment_count = len(promo.appointment_ids)
    
    @api.depends('appointment_ids', 'appointment_ids.price', 'appointment_ids.discount_amount')
    def _compute_stats(self):
        for promo in self:
            appointments = promo.appointment_ids.filtered(lambda a: a.state not in ['cancelled'])
            promo.total_discount_given = sum(appointments.mapped('discount_amount'))
            promo.total_revenue = sum(appointments.mapped('final_price'))
    
    def _compute_shareable_link(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url', '')
        for promo in self:
            promo.shareable_link = f"{base_url}/appointments?promo={promo.code}"
    
    @api.constrains('discount_type', 'discount_value')
    def _check_discount_value(self):
        for promo in self:
            if promo.discount_value <= 0:
                raise ValidationError(_('Discount value must be greater than 0'))
            if promo.discount_type == 'percentage' and promo.discount_value > 100:
                raise ValidationError(_('Percentage discount cannot exceed 100%'))
    
    @api.constrains('valid_from', 'valid_to')
    def _check_dates(self):
        for promo in self:
            if promo.valid_from and promo.valid_to and promo.valid_from > promo.valid_to:
                raise ValidationError(_('Valid From date must be before Valid To date'))
    
    @api.model
    def generate_unique_code(self, length=8):
        """Generate a unique promo code"""
        chars = string.ascii_uppercase + string.digits
        while True:
            code = ''.join(secrets.choice(chars) for _ in range(length))
            if not self.search([('code', '=', code)], limit=1):
                return code
    
    def validate_promo(self, amount=0, service_id=None, branch_id=None, partner_id=None):
        """Validate if promo code can be applied
        
        Args:
            amount: The appointment price/amount
            service_id: ID of the service (optional)
            branch_id: ID of the branch (optional)
            partner_id: ID of the partner/customer (optional)
        
        Returns: dict with 'valid', 'message', and 'discount_amount' keys
        """
        self.ensure_one()
        
        if not self.active:
            return {'valid': False, 'message': _('This promo code is no longer active'), 'discount_amount': 0}
        
        today = fields.Date.today()
        if self.valid_from and today < self.valid_from:
            return {'valid': False, 'message': _('This promo code is not yet valid'), 'discount_amount': 0}
        if self.valid_to and today > self.valid_to:
            return {'valid': False, 'message': _('This promo code has expired'), 'discount_amount': 0}
        
        if self.max_uses > 0 and self.current_uses >= self.max_uses:
            return {'valid': False, 'message': _('This promo code has reached its maximum usage limit'), 'discount_amount': 0}
        
        if partner_id and self.max_uses_per_customer > 0:
            customer_uses = self.env['custom.appointment'].search_count([
                ('promo_id', '=', self.id),
                ('partner_id', '=', partner_id),
                ('state', '!=', 'cancelled'),
            ])
            if customer_uses >= self.max_uses_per_customer:
                return {'valid': False, 'message': _('You have already used this promo code the maximum number of times'), 'discount_amount': 0}
        
        if self.minimum_amount > 0 and amount < self.minimum_amount:
            return {'valid': False, 'message': _('Minimum order amount of %s is required for this promo code') % self.minimum_amount, 'discount_amount': 0}
        
        if self.branch_ids and branch_id:
            if branch_id not in self.branch_ids.ids:
                return {'valid': False, 'message': _('This promo code is not valid for the selected branch'), 'discount_amount': 0}
        
        if self.service_ids and service_id:
            if service_id not in self.service_ids.ids:
                return {'valid': False, 'message': _('This promo code is not valid for the selected service'), 'discount_amount': 0}
        
        if self.discount_type == 'percentage':
            discount = amount * (self.discount_value / 100)
            if self.maximum_discount > 0:
                discount = min(discount, self.maximum_discount)
        else:
            discount = min(self.discount_value, amount)
        
        return {'valid': True, 'message': '', 'discount_amount': discount}
    
    def apply_promo(self):
        """Increment usage counter when promo is applied"""
        self.ensure_one()
        self.current_uses += 1
    
    def action_view_appointments(self):
        """View appointments that used this promo code"""
        self.ensure_one()
        return {
            'name': _('Appointments with %s') % self.code,
            'type': 'ir.actions.act_window',
            'res_model': 'custom.appointment',
            'view_mode': 'list,form',
            'domain': [('promo_id', '=', self.id)],
            'context': {'default_promo_id': self.id},
        }
    
    def action_copy_link(self):
        """Action to copy shareable link - returns notification"""
        self.ensure_one()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Link Copied'),
                'message': _('Shareable link: %s') % self.shareable_link,
                'type': 'success',
                'sticky': False,
            }
        }
    
    @api.model
    def get_promo_by_code(self, code):
        """Find promo by code (case-insensitive)"""
        return self.search([('code', '=ilike', code), ('active', '=', True)], limit=1)
