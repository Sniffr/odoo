from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError

class ResUsersInherit(models.Model):
    _inherit = 'res.users'

    wallet_ids = fields.One2many('user.wallet','user_id')
    wallet_id = fields.Many2one('user.wallet',compute="_compute_wallet_id",store=True)


    @api.depends('wallet_ids')
    def _compute_wallet_id(self):
        for rec in self:
            if rec.wallet_ids:
                rec.wallet_id = rec.wallet_ids[0].id
