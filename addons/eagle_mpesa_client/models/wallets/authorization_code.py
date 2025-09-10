import random

from odoo import api, fields, models

class AuthorizationCode(models.Model):
    _name = "authorization.code"

    code = fields.Char(string="authorization Code")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    funds_request_id = fields.Many2one('funds.request')
    payment_batch_id = fields.Many2one('payment.batch')
    eagle_payment_id = fields.Many2one('eagle.payment')



    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['code'] = random.randint(100000, 999999)
            # for i in range(0,3):
            #     print(vals['code'])
        result = super(AuthorizationCode, self).create(vals_list)
        
        return result