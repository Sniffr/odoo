from . import models
from . import controllers


def post_init_hook(env):
    """Activate card payment method after module installation"""
    card_method = env['payment.method'].search([('code', '=', 'card')], limit=1)
    if card_method and not card_method.active:
        card_method.active = True
