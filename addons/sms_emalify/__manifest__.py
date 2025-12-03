{
    'name': 'Emalify SMS',
    'version': '1.0',
    'summary': 'Send SMS messages using Emalify API',
    'category': 'Hidden/Tools',
    'description': """
This module allows using Emalify as a provider for SMS messaging.
Emalify is an SMS gateway service that supports sending SMS messages
to mobile numbers in Kenya and other African countries.

Configuration:
- Partner ID: Your Emalify partner ID
- API Key: Your Emalify API key
- Shortcode: Your SMS shortcode (sender ID)
- API Domain: The Emalify API endpoint (default: https://api.v2.emalify.com)
""",
    'depends': [
        'sms',
    ],
    'data': [
        'views/res_config_settings_views.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
