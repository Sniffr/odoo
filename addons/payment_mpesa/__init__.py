from . import models
from . import controllers
import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Link payment methods to providers after module installation"""
    mpesa_method = env['payment.method'].search([('code', '=', 'mpesa')], limit=1)
    if not mpesa_method:
        _logger.warning('M-Pesa module: M-Pesa payment method not found in database')
        return
    
    if not mpesa_method.active:
        mpesa_method.active = True
        _logger.info('M-Pesa module: Activated mpesa payment method (ID: %s)', mpesa_method.id)
    
    mpesa_provider = env['payment.provider'].search([('code', '=', 'mpesa')], limit=1)
    if not mpesa_provider:
        _logger.warning('M-Pesa module: M-Pesa provider not found in database')
        return
    
    if mpesa_method not in mpesa_provider.payment_method_ids:
        mpesa_provider.write({'payment_method_ids': [(4, mpesa_method.id)]})
        _logger.info('M-Pesa module: Linked M-Pesa payment method to provider')
    else:
        _logger.info('M-Pesa module: M-Pesa payment method already linked to provider')
    
    card_method = env['payment.method'].search([('code', '=', 'card')], limit=1)
    if card_method:
        if not card_method.active:
            card_method.active = True
            _logger.info('M-Pesa module: Activated card payment method (ID: %s)', card_method.id)
        
        if card_method not in mpesa_provider.payment_method_ids:
            mpesa_provider.write({'payment_method_ids': [(4, card_method.id)]})
            _logger.info('M-Pesa module: Linked card payment method to provider')
    else:
        _logger.warning('M-Pesa module: Card payment method not found in database')
