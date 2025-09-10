

from odoo import models, fields, api


class PosSession(models.Model):
    _inherit = 'pos.session'

    txn_id = fields.Char(
        string='Mpesa Txn.ID',
    )

    @api.model
    def set_txnId(self, id, txnId):
        self.env['pos.session'].browse(id).txn_id = txnId

    # def _loader_params_pos_payment_method(self):
    #     result = super()._loader_params_pos_payment_method()
    #     result['search_params']['fields'].append('is_Mpesa')
    #     result['search_params']['fields'].append('isTillPayment')
    #     return result
