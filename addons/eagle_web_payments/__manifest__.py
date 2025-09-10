# -*- coding: utf-8 -*-
{
    'name': "Eagle Mpesa Web Payments",
    'summary': "Eagle Mpesa Web Payments",
    'description': """ Eagle Mpesa Web Payments  """,
    'author': "Kola Technologies Limited",
    'website': "https://www.kolapro.com",

    'version': '18.0.0.1',
    'category': 'Accounting/Payment Providers',
    'sequence': 250,
    'support': 'support@kolapro.com',
    'live_test_url': 'https://kolapro.com/contactus',
    'depends': ['payment','website_sale','point_of_sale','eagle_mpesa_client'],



    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/backend/payment_provider_views.xml',
        'views/backend/payment_method_views.xml',



        'views/frontend/payment_method_views.xml',
        'views/frontend/payment_form.xml',

        'data/payment_method_data.xml',
        'data/payment_provider_data.xml',
        'data/email_templates.xml',

    ],
    'assets': {
        'web.assets_frontend': [
            '/eagle_web_payments/static/src/js/payment_form.js',
            '/eagle_web_payments/static/src/js/payment_custom.js',
            '/eagle_web_payments/static/src/css/payments.css',
            # '/eagle_web_payments/static/src/xml/payment_post_processing.xml',
        ],
    },
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    'license': 'LGPL-3',

    'images':[
        'static/description/banner.jpeg'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}



