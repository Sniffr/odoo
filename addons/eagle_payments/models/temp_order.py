from odoo import models, fields, api, _
import json

import logging
_logger = logging.getLogger(__name__)


class TempOrder(models.Model):
    _name = 'temp.order'
    _description = 'Temporary Order'
    _inherit = ['mail.thread']
    

    order_vals = fields.Text(
        string='order vals',
        readonly=True
    )

    transaction_id = fields.Text(
        string='transaction id',
        readonly=True
    )
    state = fields.Selection(
        string='State',
        readonly=True,
        default='draft',
        selection=[('draft', 'Draft'), ('created', 'Created')]
    )

    amount = fields.Float(
        string='Amount',
        readonly=True
    )
    
    employee_id = fields.Many2one(
        string='Agent',
        comodel_name='hr.employee',
        ondelete='restrict',
        readonly=True
    )

    def action_validate_payment(self):
        for rec in self:
            if rec.state == 'draft':
                self.env['mpesa.transaction'].action_validate_payment(
                    rec.transaction_id)

    # called in the live and test callbacks
    def create_temp_order(self, vals):
        self.create({
            'transaction_id': vals['transaction_id'], 
            'state': 'created', 
            'amount': vals['amount']})
