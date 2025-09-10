
from odoo import models,fields

class PaymentMethod(models.Model):
    _inherit = 'payment.method'

    
    internal_reference = fields.Char(
        string='Internal Reference',
    )



    def _get_compatible_payment_methods(
        self, provider_ids, partner_id, currency_id=None, force_tokenization=False,
        is_express_checkout=False, **kwargs
    ):
        
        #TODO: FIND A BETTER WAY TO OVERIDE THESE METHODS
        

        # currency = self.env['sale.order'].get_currency()

        res = super()._get_compatible_payment_methods( provider_ids, partner_id, currency_id, force_tokenization,
            is_express_checkout, **kwargs
        )


        # country = self.env['res.country'].sudo().search([("currency_id.name","=",currency)],limit=1)
     
        # partner = self.env['res.partner'].browse(partner_id)
        # countries = [partner.country_id.id,country.id]
        # domain = ['&', '&', '&', ('provider_ids', 'in', provider_ids), ('is_primary', '=', True), '|', ('supported_country_ids', '=', False), ('supported_country_ids', 'in', countries), '|', ('supported_currency_ids', '=', False), ('supported_currency_ids', 'in', [currency_id])]
        # compatible_payment_methods = self.env['payment.method'].search(domain)
        return res


    

    
