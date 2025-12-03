from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sms_provider = fields.Selection(
        related='company_id.sms_provider',
        readonly=False,
    )
    sms_emalify_api_key = fields.Char(
        related='company_id.sms_emalify_api_key',
        readonly=False,
    )
    sms_emalify_partner_id = fields.Char(
        related='company_id.sms_emalify_partner_id',
        readonly=False,
    )
    sms_emalify_shortcode = fields.Char(
        related='company_id.sms_emalify_shortcode',
        readonly=False,
    )
    sms_emalify_api_domain = fields.Char(
        related='company_id.sms_emalify_api_domain',
        readonly=False,
    )
