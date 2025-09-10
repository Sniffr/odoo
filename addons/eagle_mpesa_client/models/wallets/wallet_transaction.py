from odoo import fields, models, api, _, Command, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta,date



class WalletTransactions(models.Model):
    _name = "wallet.transaction"
    _description = "Wallet Transaction"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'image.mixin']
    _order = "custom_order asc, id asc"

    

    wallet_id = fields.Many2one('user.wallet')
    transaction_type = fields.Selection(selection=[
        ('deposit', 'Deposit'),
        ('wallet_in', 'Wallet In'),
        ('wallet_out', 'Wallet Out'),
        ('unallocated', 'Unallocated'),
        ('disbursement', 'Expense'),
    ], string="Transaction Type", tracking=True, required=True)
    amount_received = fields.Monetary(string="Amount In")
    amount_sent = fields.Monetary(string="Amount Out")
    company_id = fields.Many2one(
        'res.company', related="wallet_id.company_id", store=True)
    currency_id = fields.Many2one(related="company_id.currency_id", store=True)
    custom_order = fields.Integer(compute="_compute_custom_order", store=True)
    phone_number = fields.Char()
    # --archiving field(equivalent to delete)
    active = fields.Boolean(default=True, tracking=True, string="Unarchive")

    charged_fees = fields.Monetary(string="Charges")
    date = fields.Datetime()
    comment = fields.Char()
    sender = fields.Char()
    transaction_time = fields.Datetime()
    transaction_id = fields.Char(string="Transaction ID")
    


    @api.depends('transaction_type')
    def _compute_custom_order(self):
        for rec in self:
            if rec.transaction_type == 'deposit':
                rec.custom_order = 1
            elif rec.transaction_type == 'unallocated':
                rec.custom_order = 10000
            else:
                rec.custom_order = 10

   