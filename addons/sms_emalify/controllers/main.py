# -*- coding: utf-8 -*-

import json
import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class EmalifyController(http.Controller):
    
    @http.route('/sms/emalify/callback', type='json', auth='public', methods=['POST'], csrf=False)
    def emalify_callback(self, **kwargs):
        """
        Webhook endpoint to receive delivery status updates from Emalify.
        
        Expected callback format (adjust based on actual Emalify callback structure):
        {
            "message_id": "...",
            "status": "delivered|failed|rejected",
            "mobile": "254...",
            "delivered_at": "2024-01-01 12:00:00",
            "error": "..." (optional)
        }
        """
        try:
            # Get callback data
            callback_data = request.httprequest.get_json() or kwargs
            
            _logger.info(f'Received Emalify callback: {callback_data}')
            
            # Extract relevant information
            # Adjust these field names based on actual Emalify callback format
            message_id = callback_data.get('message_id') or callback_data.get('messageId')
            status = callback_data.get('status', '').lower()
            mobile = callback_data.get('mobile') or callback_data.get('phone_number')
            delivered_at = callback_data.get('delivered_at') or callback_data.get('deliveredAt')
            error = callback_data.get('error') or callback_data.get('error_message')
            
            if not message_id:
                _logger.warning('Emalify callback missing message_id')
                return {'success': False, 'error': 'Missing message_id'}
            
            # Map Emalify status to our status
            status_mapping = {
                'delivered': 'delivered',
                'sent': 'sent',
                'failed': 'failed',
                'rejected': 'rejected',
                'pending': 'pending',
            }
            
            mapped_status = status_mapping.get(status, 'pending')
            
            # Update delivery record
            delivery_model = request.env['sms.emalify.delivery'].sudo()
            delivery = delivery_model.update_delivery_status(
                emalify_message_id=message_id,
                status=mapped_status,
                callback_data=callback_data,
                delivered_date=delivered_at,
            )
            
            if delivery:
                _logger.info(f'Successfully updated delivery status for message {message_id}')
                return {'success': True, 'message': 'Status updated'}
            else:
                _logger.warning(f'No delivery record found for message {message_id}')
                return {'success': False, 'error': 'Delivery record not found'}
                
        except Exception as e:
            _logger.error(f'Error processing Emalify callback: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}
    
    @http.route('/sms/emalify/callback', type='http', auth='public', methods=['POST'], csrf=False)
    def emalify_callback_http(self, **kwargs):
        """
        Alternative HTTP endpoint for Emalify callbacks (in case they use form data instead of JSON).
        """
        try:
            # Try to parse as JSON first
            try:
                callback_data = json.loads(request.httprequest.data.decode('utf-8'))
            except:
                # If not JSON, use POST parameters
                callback_data = kwargs
            
            _logger.info(f'Received Emalify HTTP callback: {callback_data}')
            
            # Extract relevant information
            message_id = callback_data.get('message_id') or callback_data.get('messageId')
            status = callback_data.get('status', '').lower()
            mobile = callback_data.get('mobile') or callback_data.get('phone_number')
            delivered_at = callback_data.get('delivered_at') or callback_data.get('deliveredAt')
            error = callback_data.get('error') or callback_data.get('error_message')
            
            if not message_id:
                _logger.warning('Emalify callback missing message_id')
                return 'Missing message_id'
            
            # Map Emalify status to our status
            status_mapping = {
                'delivered': 'delivered',
                'sent': 'sent',
                'failed': 'failed',
                'rejected': 'rejected',
                'pending': 'pending',
            }
            
            mapped_status = status_mapping.get(status, 'pending')
            
            # Update delivery record
            delivery_model = request.env['sms.emalify.delivery'].sudo()
            delivery = delivery_model.update_delivery_status(
                emalify_message_id=message_id,
                status=mapped_status,
                callback_data=callback_data,
                delivered_date=delivered_at,
            )
            
            if delivery:
                _logger.info(f'Successfully updated delivery status for message {message_id}')
                return 'OK'
            else:
                _logger.warning(f'No delivery record found for message {message_id}')
                return 'Delivery record not found'
                
        except Exception as e:
            _logger.error(f'Error processing Emalify HTTP callback: {str(e)}', exc_info=True)
            return f'Error: {str(e)}'

