# -*- coding: utf-8 -*-
import logging
import requests

from odoo import _

_logger = logging.getLogger(__name__)


class SmsApiEmalify:
    """SMS API implementation for Emalify provider.
    
    This class implements the SMS API interface without inheriting from SmsApiBase
    to ensure compatibility across different Odoo versions.
    """
    
    # Mapping of provider error states to SMS failure types
    # Core mappings from Odoo's SmsApiBase + Emalify-specific states
    PROVIDER_TO_SMS_FAILURE_TYPE = {
        'server_error': 'sms_server',
        'sms_number_missing': 'sms_number_missing',
        'wrong_number_format': 'sms_number_format',
        'emalify_auth': 'sms_acc',
        'emalify_invalid_number': 'sms_number_format',
        'emalify_server_error': 'sms_server',
    }

    def __init__(self, env, account=None):
        """Initialize the SMS API.
        
        :param env: Odoo environment
        :param account: Optional IAP account (not used for Emalify)
        """
        self.env = env
        self.company = env.company

    def _set_company(self, company):
        """Set the company for this API instance.
        
        :param company: res.company record
        """
        self.company = company

    def _get_sms_api_error_messages(self):
        """Return a mapping of error states to user-friendly messages."""
        return {
            'emalify_auth': _("Emalify Authentication Error - Check your API Key, Partner ID, and Shortcode"),
            'emalify_invalid_number': _("Invalid phone number format"),
            'emalify_server_error': _("Emalify server error - Please try again later"),
        }

    def _send_sms_request(self, session, to_number, body):
        """Send a single SMS via Emalify API.
        
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
        
        # Validate configuration
        if not company_sudo.sms_emalify_api_key:
            return {'error': True, 'error_type': 'emalify_auth', 'message': 'Missing API Key'}
        if not company_sudo.sms_emalify_partner_id:
            return {'error': True, 'error_type': 'emalify_auth', 'message': 'Missing Partner ID'}
        if not company_sudo.sms_emalify_shortcode:
            return {'error': True, 'error_type': 'emalify_auth', 'message': 'Missing Shortcode'}
        
        # Build API URL
        api_domain = company_sudo.sms_emalify_domain or 'https://api.v2.emalify.com'
        api_url = f"{api_domain.rstrip('/')}/api/services/sendsms/"
        
        # Format phone number (ensure it starts with country code without +)
        formatted_number = to_number.replace('+', '').replace(' ', '').replace('-', '')
        
        data = {
            'apikey': company_sudo.sms_emalify_api_key,
            'partnerID': company_sudo.sms_emalify_partner_id,
            'mobile': formatted_number,
            'message': body,
            'shortcode': company_sudo.sms_emalify_shortcode,
            'pass_type': 'plain',
        }
        
        try:
            response = session.post(
                api_url,
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=30,
            )
            _logger.info('Emalify SMS API response: %s - %s', response.status_code, response.text)
            return response
        except requests.exceptions.Timeout:
            _logger.warning('Emalify SMS API timeout for number: %s', formatted_number)
            return {'error': True, 'error_type': 'emalify_server_error', 'message': 'Request timeout'}
        except requests.exceptions.RequestException as e:
            _logger.warning('Emalify SMS API error: %s', str(e))
            return {'error': True, 'error_type': 'emalify_server_error', 'message': str(e)}

    def _send_sms_batch(self, messages, delivery_reports_url=False):
        """Send a batch of SMS using Emalify.
        
        :param list messages: list of SMS (grouped by content) to send
        :param str delivery_reports_url: url for delivery reports (not used by Emalify)
        :return: list of results with uuid and state
        """
        session = requests.Session()
        res = []
        
        for message in messages:
            body = message.get('content') or ''
            for number_info in message.get('numbers') or []:
                uuid = number_info['uuid']
                to_number = number_info['number']
                
                fields_values = {
                    'uuid': uuid,
                    'state': 'server_error',
                    'failure_reason': _("Unknown failure at sending"),
                }
                
                response = self._send_sms_request(session, to_number, body)
                
                # Handle dict error response (from our error handling)
                if isinstance(response, dict) and response.get('error'):
                    fields_values.update({
                        'state': response.get('error_type', 'server_error'),
                        'failure_reason': response.get('message', 'Unknown error'),
                    })
                elif response is not None and hasattr(response, 'ok'):
                    try:
                        response_json = response.json() if response.text else {}
                    except Exception:
                        response_json = {}
                    
                    if response.ok:
                        # Emalify returns success
                        fields_values.update({
                            'state': 'success',
                            'failure_reason': False,
                        })
                        _logger.info('Emalify SMS sent successfully to %s', to_number)
                    else:
                        error_message = response_json.get('message') or response_json.get('error') or f'HTTP {response.status_code}'
                        fields_values.update({
                            'state': 'server_error',
                            'failure_reason': error_message,
                        })
                        _logger.warning('Emalify SMS failed for %s: %s', to_number, error_message)
                
                res.append(fields_values)
        
        return res
