# -*- coding: utf-8 -*-
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    sms_provider = fields.Selection(
        string='SMS Provider',
        selection=[
            ('iap', 'Send via Odoo'),
            ('emalify', 'Send via Emalify'),
        ],
        default='iap',
    )
    sms_emalify_api_key = fields.Char(
        string="Emalify API Key",
        groups='base.group_system',
        help="Your Emalify API Key for authentication",
    )
    sms_emalify_partner_id = fields.Char(
        string="Emalify Partner ID",
        groups='base.group_system',
        help="Your Emalify Partner ID",
    )
    sms_emalify_shortcode = fields.Char(
        string="Emalify Shortcode",
        groups='base.group_system',
        help="Your Emalify Shortcode (sender ID)",
    )
    sms_emalify_domain = fields.Char(
        string="Emalify API Domain",
        default='https://api.v2.emalify.com',
        groups='base.group_system',
        help="Emalify API domain (default: https://api.v2.emalify.com)",
    )

    def _get_sms_api_class(self):
        """Return the SMS API class based on the selected provider."""
        self.ensure_one()
        if self.sms_provider == 'emalify':
            # Lazy import to avoid circular import issues
            from odoo.addons.sms_emalify.tools.sms_api import SmsApiEmalify
            return SmsApiEmalify
        return super()._get_sms_api_class()
