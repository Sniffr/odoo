# -*- coding: utf-8 -*-
{
    'name': 'SMS Emalify',
    'version': '18.0.1.0.0',
    'category': 'Marketing/SMS Marketing',
    'summary': 'Send SMS using Emalify API',
    'description': """
SMS Emalify Integration
=======================
This module integrates Emalify SMS API with Odoo's SMS functionality.

Configuration:
- Go to Settings > General Settings > SMS section
- Select "Emalify" as your SMS provider
- Enter your API Key, Partner ID, Shortcode, and API Domain

All Odoo SMS features (contacts, marketing, notifications) will automatically use Emalify.
    """,
    'author': 'Custom',
    'website': 'https://emalify.com',
    'depends': ['sms'],
    'data': [
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
