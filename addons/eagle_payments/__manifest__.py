# -*- coding: utf-8 -*-
{
    'name': "Mpesa Odoo Payments",
    'summary': "Mpesa Odoo Payments",
    'description': """ Mpesa Odoo Payments  """,
    'author': "Kola Technologies Limited",
    'website': "https://www.kolapro.com",

    'version': '18.0.0.1',
    'category': 'Accounting/Payment Providers',
    'sequence': 250,
    'support': 'support@kolapro.com',
    'live_test_url': 'https://kolapro.com/contactus',

    # any module necessary for this one to work correctly
    'depends': ['base', 'point_of_sale','eagle_web_payments'],

    # always loaded
    'data': [
        'data/mpesa_integration_data.xml',

        'security/ir.model.access.csv',


        'views/backend/payment_methods.xml',
        # 'views/backend/pos_order_views.xml',
        # 'views/backend/temp_order_views.xml',
        'views/backend/pos_payment_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'eagle_payments/static/src/xml/MpesaPayPopup.xml',
            'eagle_payments/static/src/js/MpesaPayPopup.js',
            'eagle_payments/static/src/js/PaymentScreen.js',
        ],
    },
    'license': 'LGPL-3',

    'images':[
        'static/description/banner.jpeg'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,

}
