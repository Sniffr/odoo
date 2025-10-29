from . import models
from . import controllers
import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Create and activate payment methods for PesaPal after module installation"""
    PaymentMethod = env['payment.method'].sudo()
    
    payment_methods_data = [
        {
            'name': 'Card',
            'code': 'card',
            'active': True,
        },
        {
            'name': 'PesaPal',
            'code': 'pesapal',
            'active': True,
        },
        {
            'name': 'Mobile Money',
            'code': 'mobile_money',
            'active': True,
        },
    ]
    
    for method_data in payment_methods_data:
        existing_method = PaymentMethod.search([('code', '=', method_data['code'])], limit=1)
        
        if existing_method:
            if not existing_method.active:
                existing_method.active = True
                _logger.info('PesaPal module: Activated %s payment method (ID: %s)', method_data['name'], existing_method.id)
            else:
                _logger.info('PesaPal module: %s payment method already active (ID: %s)', method_data['name'], existing_method.id)
        else:
            new_method = PaymentMethod.create(method_data)
            _logger.info('PesaPal module: Created %s payment method (ID: %s)', method_data['name'], new_method.id)
    
    env.cr.commit()
