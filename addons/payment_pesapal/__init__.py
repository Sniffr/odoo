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
            _logger.info('PesaPal module: Activated card payment method (ID: %s)', card_method.id)
        else:
            _logger.info('PesaPal module: Card payment method already active (ID: %s)', card_method.id)
    else:
        _logger.warning('PesaPal module: Card payment method not found in database')
    
    pesapal_method = env['payment.method'].search([('code', '=', 'pesapal')], limit=1)
    if pesapal_method:
        if not pesapal_method.active:
            pesapal_method.active = True
            _logger.info('PesaPal module: Activated pesapal payment method (ID: %s)', pesapal_method.id)
        else:
            _logger.info('PesaPal module: PesaPal payment method already active (ID: %s)', pesapal_method.id)
        
        pesapal_provider = env['payment.provider'].search([('code', '=', 'pesapal')], limit=1)
        if pesapal_provider:
            bank_journals = env['account.journal'].search([('type', '=', 'bank')])
            for journal in bank_journals:
                existing_line = env['payment.method.line'].search([
                    ('payment_provider_id', '=', pesapal_provider.id),
                    ('payment_method_id', '=', pesapal_method.id),
                    ('journal_id', '=', journal.id)
                ], limit=1)
                
                if not existing_line:
                    line_vals = {
                        'name': f'PesaPal - {journal.name}',
                        'payment_provider_id': pesapal_provider.id,
                        'payment_method_id': pesapal_method.id,
                        'journal_id': journal.id,
                    }
                    env['payment.method.line'].create(line_vals)
                    _logger.info('PesaPal module: Created payment method line for journal %s', journal.name)
                else:
                    _logger.info('PesaPal module: Payment method line already exists for journal %s', journal.name)
        else:
            _logger.warning('PesaPal module: PesaPal provider not found')
    else:
        _logger.info('PesaPal module: PesaPal payment method not found (will be created by Odoo)')
