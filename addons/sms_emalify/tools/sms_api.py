import logging
import requests

from odoo import _
from odoo.addons.sms.tools.sms_api import SmsApiBase

_logger = logging.getLogger(__name__)


class SmsApiEmalify(SmsApiBase):
    """SMS API implementation for Emalify SMS gateway."""
    
    PROVIDER_TO_SMS_FAILURE_TYPE = SmsApiBase.PROVIDER_TO_SMS_FAILURE_TYPE | {
        'emalify_authentication': 'sms_credit',
        'emalify_invalid_number': 'sms_number_format',
        'emalify_insufficient_balance': 'sms_credit',
        'emalify_invalid_shortcode': 'sms_acc',
    }

    def _sms_emalify_send_request(self, session, to_number, body):
        """Send SMS via Emalify API.
        
        API Format:
        POST https://api.v2.emalify.com/api/services/sendsms/
        {
            "apikey": "your_api_key",
            "partnerID": "your_partner_id",
            "mobile": "254XXXXXXXXX",
            "message": "Your message",
            "shortcode": "YOUR_SHORTCODE",
            "pass_type": "plain"
        }
        """
        company_sudo = (self.company or self.env.company).sudo()
        
        # Get configuration from company
        api_key = company_sudo.sms_emalify_api_key
        partner_id = company_sudo.sms_emalify_partner_id
        shortcode = company_sudo.sms_emalify_shortcode
        api_domain = company_sudo.sms_emalify_api_domain or 'https://api.v2.emalify.com'
        
        if not api_key or not partner_id or not shortcode:
            _logger.warning('Emalify SMS: Missing configuration (api_key, partner_id, or shortcode)')
            return None
        
        # Normalize phone number - ensure it starts with country code
        normalized_number = self._normalize_phone_number(to_number)
        
        data = {
            'apikey': api_key,
            'partnerID': partner_id,
            'mobile': normalized_number,
            'message': body,
            'shortcode': shortcode,
            'pass_type': 'plain',
        }
        
        endpoint = f'{api_domain.rstrip("/")}/api/services/sendsms/'
        
        try:
            response = session.post(
                endpoint,
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=30,
            )
            _logger.info(f'Emalify SMS API response: {response.status_code} - {response.text}')
            return response
        except requests.exceptions.RequestException as e:
            _logger.warning('Emalify SMS API error: %s', str(e))
        return None

    def _normalize_phone_number(self, phone_number):
        """Normalize phone number to international format for Kenya.
        
        Converts:
        - 0724512285 -> 254724512285
        - +254724512285 -> 254724512285
        - 254724512285 -> 254724512285
        """
        if not phone_number:
            return phone_number
        
        # Remove any spaces, dashes, or other characters
        number = ''.join(filter(str.isdigit, str(phone_number)))
        
        # Remove leading + if present
        if phone_number.startswith('+'):
            number = phone_number[1:]
            number = ''.join(filter(str.isdigit, number))
        
        # If starts with 0, replace with 254 (Kenya country code)
        if number.startswith('0'):
            number = '254' + number[1:]
        
        # If doesn't start with country code, add 254
        if not number.startswith('254') and len(number) == 9:
            number = '254' + number
        
        return number

    def _send_sms_batch(self, messages, delivery_reports_url=False):
        """Send a batch of SMS using Emalify.
        
        See params and returns in original method sms/tools/sms_api.py
        """
        session = requests.Session()
        res = []
        
        for message in messages:
            body = message.get('content') or ''
            for number_info in message.get('numbers') or []:
                uuid = number_info['uuid']
                response = self._sms_emalify_send_request(session, number_info['number'], body)
                
                fields_values = {
                    'failure_reason': _("Unknown failure at sending, please contact support"),
                    'state': 'server_error',
                    'uuid': uuid,
                }
                
                if response is not None:
                    try:
                        response_json = response.json()
                        _logger.info(f'Emalify response JSON: {response_json}')
                        
                        # Emalify API returns different response formats
                        # Success: {"status": "success", "message": "Message sent", ...}
                        # Error: {"status": "error", "message": "Error description", ...}
                        
                        if response.ok and response_json.get('status') in ['success', 'Success', '1000', 1000]:
                            fields_values.update({
                                'failure_reason': False,
                                'failure_type': False,
                                'state': 'sent',
                            })
                        else:
                            failure_type = self._emalify_error_to_odoo_state(response_json)
                            error_message = response_json.get('message') or response_json.get('error') or self._get_sms_api_error_messages().get(failure_type)
                            fields_values.update({
                                'failure_reason': error_message,
                                'failure_type': failure_type,
                                'state': failure_type,
                            })
                    except Exception as e:
                        _logger.warning(f'Emalify SMS: Error parsing response: {e}')
                        if response.ok:
                            # If response is OK but we can't parse JSON, assume success
                            fields_values.update({
                                'failure_reason': False,
                                'failure_type': False,
                                'state': 'sent',
                            })
                
                res.append(fields_values)
        
        return res

    def _emalify_error_to_odoo_state(self, response_json):
        """Map Emalify error codes to Odoo SMS failure types."""
        status = response_json.get('status', '')
        message = response_json.get('message', '').lower()
        
        if 'authentication' in message or 'api' in message or 'invalid key' in message:
            return 'emalify_authentication'
        elif 'invalid' in message and 'number' in message:
            return 'emalify_invalid_number'
        elif 'balance' in message or 'credit' in message or 'insufficient' in message:
            return 'emalify_insufficient_balance'
        elif 'shortcode' in message:
            return 'emalify_invalid_shortcode'
        
        _logger.warning('Emalify SMS: Unknown error "%s" (status: %s)', message, status)
        return 'unknown'

    def _get_sms_api_error_messages(self):
        """Return a mapping of error types to error messages."""
        error_dict = super()._get_sms_api_error_messages()
        error_dict.update({
            'emalify_authentication': _("Emalify Authentication Error - Invalid API key or Partner ID"),
            'emalify_invalid_number': _("Invalid phone number format"),
            'emalify_insufficient_balance': _("Insufficient SMS balance on Emalify account"),
            'emalify_invalid_shortcode': _("Invalid shortcode configuration"),
            'unknown': _("Unknown error, please contact support"),
        })
        return error_dict
