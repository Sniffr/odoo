import logging
import requests
import base64
from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    mpesa_checkout_request_id = fields.Char(
        string='M-Pesa Checkout Request ID',
        readonly=True,
    )
    mpesa_phone_number = fields.Char(
        string='M-Pesa Phone Number',
        help='Phone number used for M-Pesa payment',
    )

    def _get_specific_rendering_values(self, processing_values):
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'mpesa':
            return res

        rendering_values = {
            'api_url': self.provider_id._mpesa_get_api_url(),
            'phone_number': processing_values.get('phone_number', ''),
        }
        return rendering_values

    def _mpesa_get_access_token(self):
        self.ensure_one()
        provider = self.provider_id
        api_url = provider._mpesa_get_api_url()
        
        auth_string = f"{provider.mpesa_consumer_key}:{provider.mpesa_consumer_secret}"
        auth_bytes = base64.b64encode(auth_string.encode('utf-8'))
        
        headers = {
            'Authorization': f'Basic {auth_bytes.decode("utf-8")}',
            'Content-Type': 'application/json',
        }
        
        try:
            response = requests.get(
                f'{api_url}/oauth/v1/generate?grant_type=client_credentials',
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            return response.json().get('access_token')
        except Exception as e:
            _logger.error("M-Pesa: Failed to get access token: %s", str(e))
            raise ValidationError(_("Failed to authenticate with M-Pesa. Please check your credentials."))

    def _mpesa_initiate_stk_push(self, phone_number):
        self.ensure_one()
        provider = self.provider_id
        api_url = provider._mpesa_get_api_url()
        
        access_token = self._mpesa_get_access_token()
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        
        password_string = f"{provider.mpesa_shortcode}{provider.mpesa_passkey}{timestamp}"
        password = base64.b64encode(password_string.encode('utf-8')).decode('utf-8')
        
        callback_url = provider.mpesa_callback_url
        
        payload = {
            'BusinessShortCode': provider.mpesa_shortcode,
            'Password': password,
            'Timestamp': timestamp,
            'TransactionType': 'CustomerPayBillOnline',
            'Amount': int(self.amount),
            'PartyA': phone_number,
            'PartyB': provider.mpesa_shortcode,
            'PhoneNumber': phone_number,
            'CallBackURL': callback_url,
            'AccountReference': self.reference,
            'TransactionDesc': f'Payment for {self.reference}',
        }
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
        }
        
        try:
            response = requests.post(
                f'{api_url}/mpesa/stkpush/v1/processrequest',
                json=payload,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get('ResponseCode') == '0':
                self.mpesa_checkout_request_id = result.get('CheckoutRequestID')
                self.mpesa_phone_number = phone_number
                return True
            else:
                _logger.error("M-Pesa STK Push failed: %s", result.get('ResponseDescription'))
                return False
                
        except Exception as e:
            _logger.error("M-Pesa: STK Push request failed: %s", str(e))
            return False

    def _process_notification_data(self, notification_data):
        super()._process_notification_data(notification_data)
        if self.provider_code != 'mpesa':
            return

        result_code = notification_data.get('ResultCode')
        if result_code == 0:
            self._set_done()
        else:
            self._set_canceled(
                state_message=notification_data.get('ResultDesc', 'Payment canceled or failed')
            )
