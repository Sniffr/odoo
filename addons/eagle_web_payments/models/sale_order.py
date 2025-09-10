

from odoo import _, models,fields,api

class SaleOrder(models.Model):
    _inherit = 'sale.order'


    payment_txn_id = fields.Char(
        string='Transaction ID',
    )