from . import models
from . import controllers
import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Activate card and mpesa payment methods after module installation"""
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
    else:
        _logger.warning('M-Pesa module: M-Pesa payment method not found in database')
