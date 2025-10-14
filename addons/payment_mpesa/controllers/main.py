import logging
import pprint

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class MpesaController(http.Controller):

    @http.route('/payment/mpesa/callback', type='json', auth='public', methods=['POST'], csrf=False)
    def mpesa_callback(self, **data):
        _logger.info('M-Pesa: entering callback with data:\n%s', pprint.pformat(data))
        
        try:
            body = data.get('Body', {})
            stk_callback = body.get('stkCallback', {})
            
            checkout_request_id = stk_callback.get('CheckoutRequestID')
            result_code = stk_callback.get('ResultCode')
            result_desc = stk_callback.get('ResultDesc')
            
            if not checkout_request_id:
                _logger.error('M-Pesa: No CheckoutRequestID in callback data')
                return {'ResultCode': 1, 'ResultDesc': 'Missing CheckoutRequestID'}
            
            transaction = request.env['payment.transaction'].sudo().search([
                ('mpesa_checkout_request_id', '=', checkout_request_id)
            ], limit=1)
            
            if not transaction:
                _logger.error('M-Pesa: No transaction found for CheckoutRequestID %s', checkout_request_id)
                return {'ResultCode': 1, 'ResultDesc': 'Transaction not found'}
            
            notification_data = {
                'ResultCode': result_code,
                'ResultDesc': result_desc,
                'reference': transaction.reference,
            }
            
            if result_code == 0:
                callback_metadata = stk_callback.get('CallbackMetadata', {}).get('Item', [])
                for item in callback_metadata:
                    if item.get('Name') == 'MpesaReceiptNumber':
                        notification_data['mpesa_receipt'] = item.get('Value')
                    elif item.get('Name') == 'Amount':
                        notification_data['amount'] = item.get('Value')
            
            transaction._process_notification_data(notification_data)
            
            appointment = request.env['custom.appointment'].sudo().search([
                ('payment_transaction_id', '=', transaction.id)
            ], limit=1)
            
            if appointment:
                if result_code == 0:  # Success
                    appointment.write({
                        'payment_status': 'paid',
                        'paid_amount': transaction.amount,
                        'payment_date': request.env['ir.fields'].Datetime.now(),
                        'payment_method': transaction.provider_id.name,
                        'payment_reference': transaction.reference,
                        'state': 'confirmed'
                    })
                    try:
                        appointment._send_confirmation_notifications()
                    except Exception as e:
                        _logger.warning('M-Pesa: Failed to send confirmation notifications: %s', str(e))
                else:  # Failed
                    appointment.write({
                        'payment_status': 'failed',
                        'description': f'{appointment.description or ""}\n\nPayment failed: {result_desc}'.strip()
                    })
                    _logger.info('M-Pesa: Payment failed for appointment %s. Reason: %s', appointment.id, result_desc)
            
            return {'ResultCode': 0, 'ResultDesc': 'Success'}
            
        except Exception as e:
            _logger.exception('M-Pesa: Error processing callback')
            return {'ResultCode': 1, 'ResultDesc': str(e)}

    @http.route('/payment/mpesa/initiate', type='json', auth='public')
    def mpesa_initiate_payment(self, **data):
        _logger.info('M-Pesa: initiating payment with data:\n%s', pprint.pformat(data))
        
        try:
            tx_id = data.get('tx_id')
            phone_number = data.get('phone_number', '').strip()
            
            if not phone_number:
                return {'error': 'Phone number is required'}
            
            if not phone_number.startswith('254'):
                if phone_number.startswith('0'):
                    phone_number = '254' + phone_number[1:]
                elif phone_number.startswith('+254'):
                    phone_number = phone_number[1:]
                elif phone_number.startswith('7') or phone_number.startswith('1'):
                    phone_number = '254' + phone_number
            
            if len(phone_number) != 12:
                return {'error': 'Invalid phone number format. Use 254XXXXXXXXX'}
            
            transaction = request.env['payment.transaction'].sudo().browse(tx_id)
            
            if not transaction.exists():
                return {'error': 'Transaction not found'}
            
            success = transaction._mpesa_initiate_stk_push(phone_number)
            
            if success:
                return {'success': True, 'message': 'STK Push sent to your phone'}
            else:
                return {'error': 'Failed to initiate payment. Please try again.'}
                
        except Exception as e:
            _logger.exception('M-Pesa: Error initiating payment')
            return {'error': str(e)}
