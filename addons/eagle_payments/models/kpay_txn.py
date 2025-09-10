# -*- coding: utf-8 -*-

import base64
# NEW IMPORTS

from cryptography.hazmat.primitives import padding as symmetric_padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import os
from psycopg2 import OperationalError
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from odoo import models, fields, api, _
import requests
import json
import os
import uuid
import logging
_logger = logging.getLogger(__name__)



class KpayTxn(models.AbstractModel):
    _name = 'kpay.txn'
    _description = 'Kpay Txn'

    def generate_aes_key(self):
        key = os.urandom(32)  # 256-bit key for AES-256
        return key

    def aes_encrypt_data(self, data, key):
        serialized_data = json.dumps(data).encode('utf-8')
        iv = os.urandom(16)
        padder = symmetric_padding.PKCS7(algorithms.AES.block_size).padder()
        padded_data = padder.update(serialized_data) + padder.finalize()
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv),
                        backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()
        encrypted_data = iv + ciphertext
        return base64.b64encode(encrypted_data).decode('utf-8')

    def getToken(self):
        provider = self.env['payment.provider'].sudo().search([('code','=','eagle'),('company_id','=',self.env.company.id)])

        '''
        sample result: {
                "jsonrpc": "2.0",
                "id": null,
                "result": {
                    "token_type": "bearer",
                    "access_token": "eyJzZWNyZXRfa2V5IjogIjNHdDBYdTkyRzljS3dTWlRhWEZGbzN3YWtiVlphN1Y1bVkzRGRaQW1RNUMiLCAidGltZXN0YW1wIjogMTcwOTE5Mjc5NSwgInRva2VuIjogIjc4OTNlZDYxYjM5OGQ4ZjQzZDg1MDllYjI0NjgyYzczNWVkN2E4NTciLCAidWlkIjogOX0=.OTBlNjU3ZmM3ODYzNTYwYjMwODUyZTA5MWU2ZjZkNjZkYjNlZDgzM2EyZjVjOWY4MjdlMDMyNDJmZGU3NTc3Zg==",
                    "expires_in": "180"
                }
            }
        '''
        message = {
            "client_id":provider.eagle_client_id,
        }
        key = self.generate_aes_key()
        to_send = self.aes_encrypt_data(message, key)
        signature = self._encrypt_data(key)
        
        api_key = provider.eagle_api_key
        url = provider.eagle_base_url + "/get/token"


        payload = json.dumps({
            "sent": to_send,
            "signature": signature,
        })
        headers = {
            'Target-Environment': 'test',
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}',
        }

        response = requests.request("GET", url, headers=headers, data=payload)

        response_dict = response.json()
        return response_dict.get('access_token')

    def payAndCreateSubscription(self, values):
        provider = self.env['payment.provider'].sudo().search([('code','=','eagle'),('company_id','=',self.env.company.id)])

        phone = values.get('phone')
        amount = values.get('amount')
        provider_code = values.get('provider_code')
        '''
        sample result: {
            "kola_txn_status": "Initiated",
            "transaction_id": "bd906de5-4dfe-4e5d-89e8-dffa39bb1a66"
        }
        '''

        url = provider.eagle_base_url + "/make/payment"
        _uuid = uuid.uuid4()

        message = {
            "amount": amount,
            "currency": "KES",
            "phone": phone,
            "payerMessage": "Pos Mpesa",
            "payeeNote": "Pos Mpesa",
            "provider_code": provider_code,
            "transaction_id": "{}".format(str(_uuid)),
            "support_info": {
                'reason': "Pos Mpesa"
            },
        }

        _logger.info(f"\n\ndata sent to kpay is {message}\n\n")

        auth_token = self.getToken()
        key = self.generate_aes_key()
        to_send = self.aes_encrypt_data(message, key)

        signature = self._encrypt_data(key)

        payload = json.dumps({
            "sent": to_send,
            "signature": signature,
        })

        headers = {
            'Target-Environment': 'test',
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {auth_token}',
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        return response.json()

    def _encrypt_data(self, message):
        provider = self.env['payment.provider'].sudo().search([('code','=','eagle'),('company_id','=',self.env.company.id)])

        # public_key being a char field
        self_public_key = provider.eagle_public_key
       
        public_pem = base64.b64decode(self_public_key.encode('utf-8'))

        public_key = serialization.load_pem_public_key(
            public_pem,
            backend=default_backend()
        )
        # print(message)
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

        # Convert the encrypted message to hexadecimal
        to_send = ciphertext.hex()
        return to_send
