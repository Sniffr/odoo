from odoo import fields, models, api, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
import requests
import json

import logging
_logger = logging.getLogger(__name__)


class UserWalletInherit(models.Model):
    _inherit = "user.wallet"
   

    def update_payment_provider_keys(self,vals):
        try:
            if vals.get('hippo_public_key'):
                provider = self.env['payment.provider'].sudo().search([('code','=','eagle'),('company_id','=',self.company_id.id)])
                if provider:
                    provider.sudo().write({
                        'state':'enabled',
                        'eagle_public_key': vals.get('hippo_public_key'),
                        'eagle_api_key': vals.get('hippo_api_key'),
                        'eagle_client_id': vals.get('hippo_client_id'),
                        'eagle_base_url': vals.get('hippo_base_url'),
                    })
        except Exception as e:
            _logger.info("")
            _logger.info("")
            _logger.info(e)
            _logger.info("")
            _logger.info("")

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
        except Exception as e:
            _logger.info("")
            _logger.info("")
            _logger.info(e)
            _logger.info("")
            _logger.info("")

