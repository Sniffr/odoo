

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = 'pos.order'

    txn_id = fields.Char(
        string='Mpesa Txn.ID',
    )
    txn_status = fields.Char("Txn Status")

    is_validated = fields.Boolean(
        "Validated", compute="_compute_validated", default=False)

    @api.depends('txn_status', 'txn_id')
    def _compute_validated(self):
        for rec in self:
            if rec.txn_status == "TS":
                rec.is_validated = True
            else:
                rec.is_validated = False
                

    def _action_validate(self):
        _dict = {}
        for rec in self:

            if rec.session_id.config_id.company_id.id == 2 and rec.company_id.id == 2:
                # EXCEPTION FOR RWANDA
                _logger.info("********************EXCEPTION FOR RWANDA")
                _dict = {
                    "status": "TS", "message": "Your transaction has been successfully processed"}
            else:
                response = rec.env['mpesa.transaction'].search(
                    [], limit=1).action_validate_payment(rec.txn_id)
                if "data" in response:
                    status = response['data']['transaction']['status']
                    _dict = {"status": status, "message": "status"}
                else:
                    _dict = {"status": response['status']['response_code'],
                             "message": response['status']['message']}
        return _dict

    def update_txn(self, response):
        if response['status'] == "TIP" or response['status'] == "TF" or response['status'] == "TS":
            if response['status'] == "TIP" or response['status'] == "TF":
                self.state = "draft"
            else:
                self.state = "paid"
            self.txn_status = response['status']
            return True
        else:
            return False

    def action_validate_payment(self):
        for rec in self:
            response = rec._action_validate()
            result = rec.update_txn(response)
            if not result:
                raise ValidationError(_("Code:  {} {}".format(
                    response['status'], response['message'])))

    def write(self, values):
        mpesa_method = self.payment_ids.filtered(
            lambda r: r.payment_method_id.is_Mpesa)

        methods = self.payment_ids.mapped("id")

        if "state" in values:
            # TODO:***********************ISAAC:  Validate Payment lines
            if mpesa_method:
                if values['state'] == 'paid' and mpesa_method and methods[0] == mpesa_method[0].id:
                    response = self._action_validate()
                    if response['status'] != "TS":
                        values['state'] = 'draft'

        result = super(PosOrder, self).write(values)
        return result

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if ('employee_id' in vals):
                txn_id = self.env['mpesa.transaction'].search(
                    [("employee_id", "=", vals['employee_id'])], order="create_date desc", limit=1).transaction_id

                _logger.info(
                    _("***************{}************TRANSACTION ON POS ORDER CREATE** {}**".format(txn_id, vals)))
                vals['txn_id'] = txn_id
        res = super().create(vals_list)
        return res
