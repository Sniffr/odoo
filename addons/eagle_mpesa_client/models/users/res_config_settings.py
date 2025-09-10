from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    def _get_domain(self):
        allowed_method_line_ids = self.env.company.company_expense_allowed_payment_method_line_ids
        if allowed_method_line_ids:
            return  [('id','in',allowed_method_line_ids)]
        else:
            selectable_payment_method_line_ids = self.env['account.payment.method.line'].search([
                ('payment_type', '=', 'outbound'),
                ('company_id', 'parent_of', self.env.company.id)
            ])
            return [('id','in',selectable_payment_method_line_ids.ids)]


    petty_payment_method_line_id = fields.Many2one('account.payment.method.line',domain=_get_domain,
                                        related="company_id.petty_payment_method_line_id",
                                    readonly=False,string="Petty Cash Payment Method")
    eagle_expense_category_id = fields.Many2one('product.product', related='company_id.eagle_expense_category_id', readonly=False)
    enable_kola_mpesa = fields.Boolean(related='company_id.enable_kola_mpesa', readonly=False)
    
