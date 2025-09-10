# -*- coding: utf-8 -*-
import math
from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)


class MpesaTransaction(models.Model):
    _name = 'mpesa.transaction'
    _description = 'Mpesa Transaction'
    _rec_name = 'name'
    _order = "create_date desc"
    _inherit = 'kpay.txn'

    name = fields.Char(
        string='Name',
        required=True,
        default=lambda self: _('New'),
        copy=False
    )

    employee_id = fields.Many2one(
        string='Employee',
        comodel_name='hr.employee',
        ondelete='restrict',
        required=True
    )

    transaction_id = fields.Char(
        string='Transaction Id',
        ondelete='restrict',
        required=True

    )

    def format_phone_number(self, phone_number):
        if phone_number.startswith('07'):
            return '2547' + phone_number[2:]
        elif phone_number.startswith('2547'):
            return phone_number
        else:
            raise ValidationError(_("Invalid phone number format"))

    # test txn id is: ------> "transaction_id": 'id45858967990', #Always valid transaction ID,

    @api.model
    def action_make_payment(self, phone, amount, employee_id,pos_config_id):
        pos_config = self.env['pos.config'].with_user(SUPERUSER_ID).browse(pos_config_id)
        
        """get bearer token and then charge"""
        values = {
            "phone": self.format_phone_number(phone),
            "amount":  math.ceil(amount),
            "provider_code": "mpesa",
        }
        # result['transaction_id'] = 'id45858967994' #---> simulating success
        if not employee_id:
            if self.env.user.employee_id:
                employee_id = self.env.user.employee_id.id
        if not employee_id:
            raise ValidationError("User must be linked to an employee.")

        result = self.with_company(pos_config.company_id.id).payAndCreateSubscription(values)

        _logger.info(
            "(************mpesa action_make_payment --> RETURNED INFO*****************{}***)".format(result))

        
                    
        if 'transaction_id' in result:
            self.env['mpesa.transaction'].sudo().create({
                "transaction_id": result['transaction_id'],
                "employee_id": employee_id
            })

        return result

    @api.model
    def action_validate_payment(self, txn_id):

        # get temp payment with matching txn_id
        temp_payment = self.env['temp.order'].search(
            [('transaction_id', '=', txn_id)], limit=1)

        if temp_payment:
            return {
                'status': 'TS',
            }
        else:
            return {
                'status': 'TIP',
            }

    @api.model
    def action_validate_till_payment(self, amount):

        # get temp payment with matching txn_id
        temp_payment = self.env['temp.order'].search(
            [('amount', '=', amount)], limit=1)

        if temp_payment:
            return {
                'status': 'TS',
            }
        else:
            return {
                'status': 'TIP',
            }
