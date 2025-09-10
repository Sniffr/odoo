from odoo import fields, models, api, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
import requests
import json

import logging
_logger = logging.getLogger(__name__)


class UserWalletInherit(models.Model):
    _inherit = "user.wallet"
   

    

    def send_to_other_channels(self,vals_dict):
        try:
            transaction = self.env['payment.transaction'].sudo().search([('eagle_transaction_id','=',vals_dict.get('transaction_id'))])
            if transaction:
                payload = json.dumps(vals_dict)
                url = f"{self.company_id.sudo().get_base_url()}/payment/eagle/webhook"
                headers = {
                    'Content-Type': 'application/json',
                }
                for i in range(0,2):
                    _logger.info("")
                _logger.info(payload)
                for i in range(0,2):
                    _logger.info("")
                response = requests.request("POST", url, headers=headers, data=payload) 
            else:
                payload = json.dumps(vals_dict)
                url = f"{self.company_id.sudo().get_base_url()}/kpay-callback"
                headers = {
                    'Content-Type': 'application/json',
                }
                for i in range(0,2):
                    _logger.info("")
                _logger.info(payload)
                for i in range(0,2):
                    _logger.info("")
                response = requests.request("POST", url, headers=headers, data=payload)

        except Exception as e:
            _logger.info("")
            _logger.info("")
            _logger.info(e)
            _logger.info("")
            _logger.info("")

