from odoo import api, fields, models, _


class PosPayment(models.Model):
    _inherit = 'pos.payment'

    transaction_id = fields.Char(
        'Payment Transaction ID', related="pos_order_id.txn_id")

    mpesa_money_id = fields.Char(
        string='Mpesa Transaction ID', readonly=True, compute="_compute_mpesa_money_id", store=True
    )

    @api.depends("pos_order_id.txn_id", "transaction_id")
    def _compute_mpesa_money_id(self):
        for rec in self:
            if rec.pos_order_id.txn_id:
                response = self.env['mpesa.transaction'].action_validate_payment(
                    rec.pos_order_id.txn_id)
                if "data" in response:
                    rec.mpesa_money_id = response['data']['transaction']['mpesa_money_id']
                else:
                    rec.mpesa_money_id = ""

    def compute_mpesa_txn(self):
        records = self.env['pos.payment'].search(
            [("payment_method_id.is_Mpesa", "=", True)])
        for rec in records:
            response = self.env['mpesa.transaction'].action_validate_payment(
                rec.transaction_id)
            if "data" in response:
                rec.mpesa_money_id = response['data']['transaction']['mpesa_money_id']
            else:
                rec.mpesa_money_id = ""
