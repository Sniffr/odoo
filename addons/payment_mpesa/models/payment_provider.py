from odoo import _, api, fields, models


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('mpesa', 'M-Pesa')],
        ondelete={'mpesa': 'set default'}
    )
    
    mpesa_consumer_key = fields.Char(
        string='Consumer Key',
        required_if_provider='mpesa',
        groups='base.group_system',
    )
    mpesa_consumer_secret = fields.Char(
        string='Consumer Secret',
        required_if_provider='mpesa',
        groups='base.group_system',
    )
    mpesa_shortcode = fields.Char(
        string='Business Shortcode',
        required_if_provider='mpesa',
        help='Your M-Pesa Paybill or Till Number',
    )
    mpesa_passkey = fields.Char(
        string='Passkey',
        required_if_provider='mpesa',
        groups='base.group_system',
        help='M-Pesa Online Passkey',
    )
    mpesa_callback_url = fields.Char(
        string='Callback URL',
        compute='_compute_mpesa_callback_url',
        help='URL where M-Pesa will send payment notifications',
    )

    @api.depends('code')
    def _compute_mpesa_callback_url(self):
        for provider in self:
            if provider.code == 'mpesa':
                base_url = provider.get_base_url()
                provider.mpesa_callback_url = f'{base_url}/payment/mpesa/callback'
            else:
                provider.mpesa_callback_url = False

    def _mpesa_get_api_url(self):
        self.ensure_one()
        if self.state == 'enabled':
            return 'https://api.safaricom.co.ke'
        else:
            return 'https://sandbox.safaricom.co.ke'
