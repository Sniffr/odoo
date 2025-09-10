# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import pprint

import requests
from werkzeug.urls import url_join
from odoo.http import request
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from odoo.addons.eagle_web_payments import const
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding  
from cryptography.hazmat.primitives import padding as symmetric_padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import base64
import json
import requests
import re
import uuid
import os


_logger = logging.getLogger(__name__)


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('eagle', "kPay")], ondelete={'eagle': 'set default'}
    )
    eagle_public_key = fields.Char(
        string="Eagle Public Key",
        help="The key solely used to encrypt eagle payload.",
        required_if_provider='eagle',
    )
    eagle_api_key = fields.Char(
        string="Eagle API Key",
        required_if_provider='eagle',
        groups='base.group_system',
    )
    eagle_client_id = fields.Char(
        string="Eagle Client ID",
        required_if_provider='eagle',
        groups='base.group_system',
    )

    eagle_base_url = fields.Char(
        string="Eagle URL",
        required_if_provider='eagle',
        groups='base.group_system',
    )
    #======REQUEST METHODS=====#

    def fix_phone_number(self,phone,type):
        match = re.match(r'\((\d{3})\) (\d{3})-(\d{3})', phone)
        if match:
            fixed_number =  ''.join(match.groups())
            if type == "eagle_mpesa":
                fixed_number = "254"+fixed_number
            return fixed_number
        else:
            return phone
        

    #ENCRYPTION METHODS

    def generate_aes_key(self):
        key = os.urandom(32)  # 256-bit key for AES-256
        return key

    def aes_encrypt_data(self,data, key):
        serialized_data = json.dumps(data).encode('utf-8')
        iv = os.urandom(16)
        padder = symmetric_padding.PKCS7(algorithms.AES.block_size).padder()
        padded_data = padder.update(serialized_data) + padder.finalize()
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()
        encrypted_data = iv + ciphertext
        return base64.b64encode(encrypted_data).decode('utf-8')
    

    def _encrypt_data(self,message):
        try:
            self_public_key = self.eagle_public_key
            public_pem = base64.b64decode(self_public_key.encode('utf-8'))
            
            public_key  = serialization.load_pem_public_key(
                public_pem,
                backend=default_backend()
            )
            if isinstance(message, dict):
                message = json.dumps(message)
                message = message.encode()
            ciphertext = public_key.encrypt(
                message,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )        
            to_send = ciphertext.hex()
            return to_send
        
        except Exception as e:
            print("Encryption failed:", e)
    


    def _request_bearer_token(self,url):
        try:
            message = {
                "client_id":self.eagle_client_id,
            }
            key = self.generate_aes_key()
            to_send = self.aes_encrypt_data(message,key)
            signature = self._encrypt_data(key)
            api_key = self.eagle_api_key

            url = url+"/get/token"

            payload = json.dumps({
                "sent": to_send,
                "signature":signature,
            })
            headers = {
                'Target-Environment': 'test',
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {api_key}',
            }
            response = requests.request("GET", url, headers=headers, data=payload)
            response_dict = response.json()


            return response_dict.get('access_token')
        except Exception as e:
            _logger.info("\n\n {}\n\n".format(e))
            return False

        
    def _make_payment_request(self,payload):
        try:
            txn_id = str(uuid.uuid4())+"BSP"
            phone_no = self.fix_phone_number(payload['phone'],payload['txn'].payment_method_id.code)
            user  = request.env['res.users'].browse(request.uid)

            current_host_url = request.httprequest.host_url

            provider_code = payload['txn'].payment_method_id.code
            mpesa_type = False
            if provider_code == "eagle_mpesa":
                currency = "KES"
                amount = str(int(payload['txn'].amount))
                mpesa_type = "stk_push"
                phone_no = "254"+str(phone_no)
            else:
                amount = str(payload['txn'].amount)
                currency = "UGX"

            _logger.info(f"\n\n TRANSACTION:ID{txn_id} \n\n")

            if provider_code == "eagle_mpesa":
                provider_code = "mpesa"
            elif provider_code == "eagle_mtn":
                provider_code = "mtn"
            elif provider_code == "eagle_airtel":
                provider_code = "airtel"

            message = {
                "amount": amount,
                "currency": currency,
                "phone":phone_no,
                "payerMessage": "PAYMENT FOR BSP",
                "payeeNote": "PAYMENT FOR BSP",
                "provider_code":provider_code,
                "transaction_id":txn_id,
                "support_info":{
                    "phone": phone_no,
                    "code":"BSP",
                    "uid": request.uid,
                    
                }
               
            }

            if mpesa_type:
                message["support_info"]['mpesa_type'] = mpesa_type
                _logger.info("here")



            _logger.info("here")





            _logger.info(f"\n\nPAYLOAD: {payload} \n\n")

            #update eagle TransactionID 
            payload['txn'].sudo().write({
                "eagle_transaction_id":txn_id,
                "eagle_mobile":phone_no,
                "mpesa_type":mpesa_type
            })

            _logger.info(f"\n\n TRANSACTION:ID{txn_id} : and {payload['txn']} and {payload['txn'].eagle_transaction_id}\n\n")




            token = payload['token']

            key = self.generate_aes_key()
            to_send = self.aes_encrypt_data(message,key)

            url = self.eagle_base_url + "/make/payment"

            signature = self._encrypt_data(key)
            payload = json.dumps({
                "sent": to_send,
                "signature":signature,
            })

            headers = {
                'Target-Environment': 'test',
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}',
            }
            # return 

            _logger.info(f"\nmessage*SENT** {json.dumps(message, indent=4)}\n")
            
            response = requests.request("POST", url, headers=headers, data=payload)
            return response.json()
        

        except Exception as e:
            _logger.info(f"\n\n KPAY ERROR MAKE REQUEST {e} \n\n")
            return False




    #=== COMPUTE METHODS ===#

    def _compute_feature_support_fields(self):
        """ Override of `payment` to enable additional features. """
        super()._compute_feature_support_fields()
        self.filtered(lambda p: p.code == 'eagle').update({
            'support_tokenization': True,
        })

    # === BUSINESS METHODS ===#

    @api.model
    def _get_compatible_providers(self, *args, is_validation=False, **kwargs):
        """ Override of `payment` to filter out kPay providers for validation operations. """
        providers = super()._get_compatible_providers(*args, is_validation=is_validation, **kwargs)

        if is_validation:
            providers = providers.filtered(lambda p: p.code != 'eagle')

        return providers

    def _get_supported_currencies(self):
        """ Override of `payment` to return the supported currencies. """
        supported_currencies = super()._get_supported_currencies()
        if self.code == 'eagle':
            supported_currencies = supported_currencies.filtered(
                lambda c: c.name in const.SUPPORTED_CURRENCIES
            )
        return supported_currencies
    
  

    def _eagle_make_request(self, endpoint, payload=None, method='POST'):

        """ Make a request to kPay API at the specified endpoint."""
        self.ensure_one()

        base_url = self.eagle_base_url
             #Request for Bearer Token
        bearerToken = self._request_bearer_token(base_url)
        payload['token'] = bearerToken
        response = self._make_payment_request(payload)

        return response


    def _get_default_payment_method_codes(self):
        """ Override of `payment` to return the default payment method codes. """
        default_codes = super()._get_default_payment_method_codes()
        if self.code != 'eagle':
            return default_codes
        return const.DEFAULT_PAYMENT_METHODS_CODES
