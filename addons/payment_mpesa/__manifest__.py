{
    'name': 'Payment Provider: M-Pesa',
    'version': '1.0',
    'category': 'Accounting/Payment Providers',
    'sequence': 350,
    'summary': 'M-Pesa Payment Gateway for Safaricom Kenya',
    'description': """
M-Pesa Payment Provider
=======================
This module adds M-Pesa as a payment provider in Odoo.
Supports M-Pesa STK Push (Lipa Na M-Pesa Online) for seamless mobile payments.

Features:
- STK Push for instant mobile payment requests
- Payment status checking
- Transaction verification
- Support for Kenyan mobile numbers
    """,
    'depends': ['payment'],
    'data': [
        'views/payment_mpesa_templates.xml',
        'views/payment_provider_views.xml',
        'data/payment_provider_data.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'payment_mpesa/static/src/js/payment_form.js',
        ],
    },
    'application': False,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'post_init_hook': 'post_init_hook',
}
