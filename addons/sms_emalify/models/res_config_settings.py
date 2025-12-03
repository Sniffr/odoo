# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sms_provider = fields.Selection(
        related='company_id.sms_provider',
        readonly=False,
        string="SMS Provider",
    )
    sms_emalify_api_key = fields.Char(
        related='company_id.sms_emalify_api_key',
        readonly=False,
        string="Emalify API Key",
    )
    sms_emalify_partner_id = fields.Char(
        related='company_id.sms_emalify_partner_id',
        readonly=False,
        string="Emalify Partner ID",
    )
    sms_emalify_shortcode = fields.Char(
        related='company_id.sms_emalify_shortcode',
        readonly=False,
        string="Emalify Shortcode",
    )
    sms_emalify_domain = fields.Char(
        related='company_id.sms_emalify_domain',
        readonly=False,
        string="Emalify API Domain",
    )
