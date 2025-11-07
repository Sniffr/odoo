from . import models
from . import controllers
import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Activate payment methods and create payment method lines after module installation"""
    card_method = env['payment.method'].search([('code', '=', 'card')], limit=1)
    if card_method:
        if not card_method.active:
            card_method.active = True
            _logger.info('M-Pesa module: Activated card payment method (ID: %s)', card_method.id)
        else:
            _logger.info('M-Pesa module: Card payment method already active (ID: %s)', card_method.id)
    else:
        _logger.warning('M-Pesa module: Card payment method not found in database')
    
    mpesa_method = env['payment.method'].search([('code', '=', 'mpesa')], limit=1)
    if mpesa_method:
        if not mpesa_method.active:
            mpesa_method.active = True
            _logger.info('M-Pesa module: Activated mpesa payment method (ID: %s)', mpesa_method.id)
        else:
            _logger.info('M-Pesa module: M-Pesa payment method already active (ID: %s)', mpesa_method.id)
        
        mpesa_provider = env['payment.provider'].search([('code', '=', 'mpesa')], limit=1)
        if mpesa_provider:
            bank_journals = env['account.journal'].search([('type', '=', 'bank')])
            for journal in bank_journals:
                existing_line = env['payment.method.line'].search([
                    ('payment_provider_id', '=', mpesa_provider.id),
                    ('payment_method_id', '=', mpesa_method.id),
                    ('journal_id', '=', journal.id)
                ], limit=1)
                
                if not existing_line:
                    line_vals = {
                        'name': f'M-Pesa - {journal.name}',
                        'payment_provider_id': mpesa_provider.id,
                        'payment_method_id': mpesa_method.id,
                        'journal_id': journal.id,
                    }
                    env['payment.method.line'].create(line_vals)
                    _logger.info('M-Pesa module: Created payment method line for journal %s', journal.name)
                else:
                    _logger.info('M-Pesa module: Payment method line already exists for journal %s', journal.name)
        else:
            _logger.warning('M-Pesa module: M-Pesa provider not found')
    else:
        _logger.warning('M-Pesa module: M-Pesa payment method not found in database')
