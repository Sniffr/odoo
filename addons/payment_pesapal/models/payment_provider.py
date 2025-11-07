from odoo import _, api, fields, models


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('pesapal', 'PesaPal')],
        ondelete={'pesapal': 'set default'}
    )
    
    pesapal_consumer_key = fields.Char(
        string='Consumer Key',
        required_if_provider='pesapal',
        groups='base.group_system',
    )
    pesapal_consumer_secret = fields.Char(
        string='Consumer Secret',
        required_if_provider='pesapal',
        groups='base.group_system',
    )
    pesapal_ipn_url = fields.Char(
        string='IPN URL',
        compute='_compute_pesapal_ipn_url',
        store=True,
        readonly=False,
        help='URL where PesaPal will send payment notifications (IPN). Auto-computed but can be overridden manually.',
    )
    pesapal_api_url = fields.Char(
        string='API URL',
        compute='_compute_pesapal_api_url',
        help='PesaPal API endpoint (Production or Sandbox)',
    )

    @api.depends('code')
    def _compute_pesapal_ipn_url(self):
        for provider in self:
            if provider.code == 'pesapal' and not provider.pesapal_ipn_url:
                base_url = provider.get_base_url()
                provider.pesapal_ipn_url = f'{base_url}/payment/pesapal/ipn'
            elif provider.code != 'pesapal':
                provider.pesapal_ipn_url = False

    @api.depends('state')
    def _compute_pesapal_api_url(self):
        for provider in self:
            if provider.code == 'pesapal':
                if provider.state == 'enabled':
                    provider.pesapal_api_url = 'https://pay.pesapal.com/v3'
                else:
                    provider.pesapal_api_url = 'https://cybqa.pesapal.com/pesapalv3'
            else:
                provider.pesapal_api_url = False
    
    def action_reset_ipn_url(self):
        """Reset IPN URL to the default computed value"""
        self.ensure_one()
        if self.code == 'pesapal':
            base_url = self.get_base_url()
            self.pesapal_ipn_url = f'{base_url}/payment/pesapal/ipn'
        return True

    def _pesapal_get_api_url(self):
        """Get PesaPal API URL based on provider state"""
        self.ensure_one()
        if self.state == 'enabled':
            return 'https://pay.pesapal.com/v3'
        else:
            return 'https://cybqa.pesapal.com/pesapalv3'
    
    def _get_supported_payment_method_codes(self):
        """Return the payment method codes supported by this provider"""
        res = super()._get_supported_payment_method_codes()
        if self.code == 'pesapal':
            res.append('pesapal')
        return res
