from odoo import fields, models, api, _

class ResCompanyInheirt(models.Model):
    _inherit = 'res.company'

    eagle_user_name = fields.Char()
    eagle_api_key = fields.Char()
    hippo_public_key = fields.Char(
        string="Public Key",
        copy=False,
        help="The key solely used to encrypt hippo payload.",
    )
    hippo_api_key = fields.Char(
        string="API Key",
        copy=False,
    )
    hippo_client_id = fields.Char(
        string="Client ID",
        copy=False,
    )

   