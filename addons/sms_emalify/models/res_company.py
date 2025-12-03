from odoo import fields, models

from odoo.addons.sms_emalify.tools.sms_api import SmsApiEmalify


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
        help="Your Emalify API key for authentication"
    )
    sms_emalify_partner_id = fields.Char(
        string="Emalify Partner ID",
        groups='base.group_system',
        help="Your Emalify Partner ID"
    )
    sms_emalify_shortcode = fields.Char(
        string="Emalify Shortcode",
        groups='base.group_system',
        help="Your SMS sender ID / shortcode (e.g., STDIOXTIX)"
    )
    sms_emalify_api_domain = fields.Char(
        string="Emalify API Domain",
        default='https://api.v2.emalify.com',
        groups='base.group_system',
        help="The Emalify API endpoint domain"
    )

    def _get_sms_api_class(self):
        self.ensure_one()
        if self.sms_provider == 'emalify':
            return SmsApiEmalify
        return super()._get_sms_api_class()
