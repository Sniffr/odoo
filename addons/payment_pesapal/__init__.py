from . import models
from . import controllers
import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Activate card and pesapal payment methods after module installation"""
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
    else:
        _logger.info('PesaPal module: PesaPal payment method not found (will be created by Odoo)')
