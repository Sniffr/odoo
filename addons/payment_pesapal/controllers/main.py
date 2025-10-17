import logging
import requests
from odoo import http, fields
from odoo.http import request

_logger = logging.getLogger(__name__)


class PesaPalController(http.Controller):

    @http.route('/payment/pesapal/return', type='http', auth='public', methods=['GET'], csrf=False)
    def pesapal_return(self, **data):
        """Handle return from PesaPal hosted checkout"""
        _logger.info('PesaPal: Customer returned from checkout with data: %s', data)
        
        tracking_id = data.get('OrderTrackingId')
        merchant_ref = data.get('OrderMerchantReference')
        
        if not tracking_id:
            return request.redirect('/payment/process')
        
        tx = request.env['payment.transaction'].sudo().search([
            ('pesapal_order_tracking_id', '=', tracking_id)
        ], limit=1)
        
        if not tx:
            _logger.warning('PesaPal: Transaction not found for tracking ID: %s', tracking_id)
            return request.redirect('/payment/process')
        
        status = self._get_transaction_status(tx.provider_id, tracking_id)
        
        if status:
            notification_data = {
                'OrderTrackingId': tracking_id,
                'OrderMerchantReference': merchant_ref,
                'status_code': status.get('payment_status_code'),
                'status_description': status.get('description')
            }
            
            tx._handle_notification_data('pesapal', notification_data)
        
        appointment = request.env['custom.appointment'].sudo().search([
            ('payment_transaction_id', '=', tx.id)
        ], limit=1)
        
        if appointment:
            if tx.state == 'done':
                appointment.write({
                    'payment_status': 'paid',
                    'paid_amount': tx.amount,
                    'payment_date': fields.Datetime.now(),
                    'payment_method': tx.provider_id.name,
                    'payment_reference': tx.reference,
                    'state': 'confirmed'
                })
                try:
                    appointment._send_confirmation_notifications()
                except Exception as e:
                    _logger.warning('Failed to send confirmation notifications: %s', str(e))
                
                return request.redirect(f'/appointments/payment/success?appointment_id={appointment.id}')
            elif tx.state in ['cancel', 'error']:
                appointment.write({
                    'payment_status': 'failed'
                })
                return request.redirect(f'/appointments/payment?appointment_id={appointment.id}&error=Payment failed. Please try again.')
        
        return request.redirect('/appointments/payment/success' if tx.state == 'done' else '/appointments')

    @http.route('/payment/pesapal/ipn', type='http', auth='public', methods=['GET'], csrf=False)
    def pesapal_ipn(self, **data):
        """Handle IPN (Instant Payment Notification) from PesaPal"""
        _logger.info('PesaPal: IPN received with data: %s', data)
        
        tracking_id = data.get('OrderTrackingId')
        merchant_ref = data.get('OrderMerchantReference')
        
        if not tracking_id:
            return 'Invalid notification'
        
        tx = request.env['payment.transaction'].sudo().search([
            ('pesapal_order_tracking_id', '=', tracking_id)
        ], limit=1)
        
        if not tx:
            _logger.warning('PesaPal IPN: Transaction not found for tracking ID: %s', tracking_id)
            return 'Transaction not found'
        
        status = self._get_transaction_status(tx.provider_id, tracking_id)
        
        if status:
            notification_data = {
                'OrderTrackingId': tracking_id,
                'OrderMerchantReference': merchant_ref,
                'status_code': status.get('payment_status_code'),
                'status_description': status.get('description')
            }
            
            try:
                tx._handle_notification_data('pesapal', notification_data)
                _logger.info('PesaPal IPN: Transaction %s processed successfully', tracking_id)
            except Exception as e:
                _logger.error('PesaPal IPN: Error processing transaction %s: %s', tracking_id, str(e))
                return 'Error processing transaction'
        
        return 'OK'

    def _get_transaction_status(self, provider, tracking_id):
        """Get transaction status from PesaPal API"""
        api_url = provider._pesapal_get_api_url()
        auth_url = f'{api_url}/api/Auth/RequestToken'
        
        payload = {
            'consumer_key': provider.pesapal_consumer_key,
            'consumer_secret': provider.pesapal_consumer_secret
        }
        
        try:
            response = requests.post(auth_url, json=payload, headers={'Content-Type': 'application/json'})
            response.raise_for_status()
            token = response.json().get('token')
            
            if not token:
                _logger.error('PesaPal: Failed to get auth token')
                return None
            
            status_url = f'{api_url}/api/Transactions/GetTransactionStatus?orderTrackingId={tracking_id}'
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(status_url, headers=headers)
            response.raise_for_status()
            status_data = response.json()
            
            _logger.info('PesaPal: Transaction status for %s: %s', tracking_id, status_data)
            return status_data
            
        except Exception as e:
            _logger.error('PesaPal: Failed to get transaction status: %s', str(e))
            return None
