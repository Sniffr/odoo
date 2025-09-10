from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError

class ResCompanyInherit(models.Model):
    _inherit = 'res.company'

    petty_payment_method_line_id = fields.Many2one('account.payment.method.line',string="Petty Cash Payment Method")
    eagle_expense_category_id = fields.Many2one(
        "product.product",
        string="Eagle Company Expense Category",
        check_company=True,
        domain="[('can_be_expensed','=',True)]",
        help="The company's default expense category when an eagle expense is created.",
    )
    enable_kola_mpesa = fields.Boolean()