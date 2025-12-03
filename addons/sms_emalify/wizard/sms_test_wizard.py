# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class SmsEmalifyTestWizard(models.TransientModel):
    _name = 'sms.emalify.test.wizard'
    _description = 'Test Emalify SMS Connection'

    phone_number = fields.Char(
        string='Test Phone Number',
        required=True,
        help='Enter a phone number to send a test SMS (e.g., 254724512285 or +254724512285)'
    )
    
    message = fields.Text(
        string='Test Message',
        default='This is a test SMS from Odoo via Emalify. If you receive this, your configuration is working correctly!',
        required=True,
        help='Message to send for testing'
    )
    
    result = fields.Text(
        string='Result',
        readonly=True,
        help='Result of the test'
    )
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('error', 'Error'),
    ], default='draft', string='State')

    @api.constrains('phone_number')
    def _check_phone_number(self):
        """Validate phone number format"""
        for wizard in self:
            if wizard.phone_number:
                # Remove spaces and special characters for validation
                import re
                cleaned = re.sub(r'[^\d+]', '', wizard.phone_number)
                if len(cleaned) < 9:
                    raise ValidationError(_('Phone number is too short. Please enter a valid phone number.'))

    def action_send_test_sms(self):
        """Send a test SMS via Emalify"""
        self.ensure_one()
        
        try:
            # Get configuration
            IrConfigParam = self.env['ir.config_parameter'].sudo()
            emalify_enabled = IrConfigParam.get_param('sms_emalify.enabled', 'False') == 'True'
            
            if not emalify_enabled:
                raise UserError(_(
                    'Emalify SMS is not enabled. Please enable it in Settings → General Settings → Emalify SMS.'
                ))
            
            api_key = IrConfigParam.get_param('sms_emalify.api_key', '')
            partner_id = IrConfigParam.get_param('sms_emalify.partner_id', '')
            shortcode = IrConfigParam.get_param('sms_emalify.shortcode', '')
            
            if not all([api_key, partner_id, shortcode]):
                raise UserError(_(
                    'Emalify SMS credentials are incomplete. Please configure all required fields in Settings.'
                ))
            
            # Format phone number
            sms_sms = self.env['sms.sms']
            formatted_number = sms_sms._emalify_format_phone_number(self.phone_number)
            
            if not formatted_number:
                raise UserError(_(
                    'Invalid phone number format. Please enter a valid phone number (e.g., 254724512285 or +254724512285).'
                ))
            
            # Send test SMS
            _logger.info(f'Sending test SMS to {formatted_number}')
            
            response = sms_sms._emalify_send_sms(
                api_key=api_key,
                partner_id=partner_id,
                shortcode=shortcode,
                mobile=formatted_number,
                message=self.message,
                pass_type=IrConfigParam.get_param('sms_emalify.pass_type', 'plain'),
            )
            
            # Create delivery tracking record
            self.env['sms.emalify.delivery'].sudo().create({
                'phone_number': formatted_number,
                'message_content': self.message,
                'status': 'sent',
                'emalify_message_id': response.get('message_id', ''),
                'api_response': str(response),
                'res_model': self._name,
                'res_id': self.id,
            })
            
            # Update wizard state
            self.write({
                'state': 'sent',
                'result': f'✓ Test SMS sent successfully to {formatted_number}!\n\n'
                         f'API Response:\n{str(response)}\n\n'
                         f'Please check your phone for the message. '
                         f'If you configured the callback URL in Emalify dashboard, '
                         f'you can check the delivery status in the Delivery Logs.'
            })
            
            _logger.info(f'Test SMS sent successfully to {formatted_number}')
            
            return {
                'type': 'ir.actions.act_window',
                'res_model': self._name,
                'res_id': self.id,
                'view_mode': 'form',
                'target': 'new',
            }
            
        except Exception as e:
            error_message = str(e)
            _logger.error(f'Test SMS failed: {error_message}', exc_info=True)
            
            self.write({
                'state': 'error',
                'result': f'✗ Test SMS failed!\n\nError:\n{error_message}\n\n'
                         f'Please check:\n'
                         f'1. Your API credentials are correct\n'
                         f'2. Your Emalify account has sufficient credit\n'
                         f'3. The phone number is valid\n'
                         f'4. Your network connection is working\n'
                         f'5. Check the Odoo logs for more details'
            })
            
            return {
                'type': 'ir.actions.act_window',
                'res_model': self._name,
                'res_id': self.id,
                'view_mode': 'form',
                'target': 'new',
            }
    
    def action_reset(self):
        """Reset the wizard to send another test"""
        self.ensure_one()
        self.write({
            'state': 'draft',
            'result': False,
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

