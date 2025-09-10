# Part of Odoo. See LICENSE file for full copyright and licensing details.

# The currencies supported by pesapal, in ISO 4217 format.
# See https://www.pesapal.com/blog/simplify-payments-operations-at-your-hotel-with-the-resrequest-pesapal-partnership
# Last seen online: 30 October 2023.
SUPPORTED_CURRENCIES = [
    'GBP',
    'CAD',
    'CLP',
    'COP',
    'EGP',
    'EUR',
    'GHS',
    'GNF',
    'KES',
    'MWK',
    'MAD',
    'NGN',
    'RWF',
    'SLL',
    'STD',
    'ZAR',
    'TZS',
    'UGX',
    'USD',
    'XAF',
    'XOF',
    'ZMW',
]


# Mapping of transaction states to mtn payment statuses.
PAYMENT_STATUS_MAPPING = {
    'pending': ['pending auth'],
    'done': ['successful'],
    'cancel': ['cancelled'],
    'error': ['failed'],
}
