

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    is_Mpesa = fields.Boolean(
        string='Is Mpesa Pay',
    )
    isTillPayment = fields.Boolean(
        string='Is Mpesa Pay Bill',
    )

    @api.onchange('is_Mpesa')
    def _onchange_is_Mpesa(self):
        if self.is_Mpesa:
            mpesa = self.search([('is_Mpesa', '=', True)])
            if mpesa and mpesa[0].id != self.id.origin:
                raise UserError(_('Mpesa already set'))
            self.isTillPayment = False

    @api.onchange('isTillPayment')
    def _onchange_isTillPayment(self):
        if self.isTillPayment:
            till_pay = self.search([('isTillPayment', '=', True)])
            if till_pay and till_pay[0].id != self.id.origin:
                raise UserError(_('Pay Bill already set'))
            self.is_Mpesa = False

    @api.model
    def _load_pos_data_fields(self, config_id):
        result = super()._load_pos_data_fields(config_id)
        result.append('is_Mpesa')
        result.append('isTillPayment')
        return result
