from collections import defaultdict

from odoo import fields, models


class SmsSms(models.Model):
    _inherit = 'sms.sms'

    failure_type = fields.Selection(
        selection_add=[
            ('emalify_authentication', 'Emalify Authentication Error'),
            ('emalify_invalid_number', 'Invalid Phone Number'),
            ('emalify_insufficient_balance', 'Insufficient Balance'),
            ('emalify_invalid_shortcode', 'Invalid Shortcode'),
        ],
    )

    def _split_by_api(self):
        """Override to handle Emalify provider choice, which is company dependent."""
        sms_by_company = defaultdict(lambda: self.env['sms.sms'])
        todo_via_super = self.browse()
        
        for sms in self:
            company = sms._get_sms_company()
            sms_by_company[company] += sms
        
        for company, company_sms in sms_by_company.items():
            if company.sms_provider == 'emalify':
                sms_api = company._get_sms_api_class()(self.env)
                sms_api._set_company(company)
                yield sms_api, company_sms
            else:
                todo_via_super += company_sms
        
        if todo_via_super:
            yield from super(SmsSms, todo_via_super)._split_by_api()

    def _get_batch_size(self):
        """Return batch size for Emalify SMS sending."""
        companies = self._get_sms_company()
        if companies and any(company.sms_provider == 'emalify' for company in companies):
            return int(self.env['ir.config_parameter'].sudo().get_param('sms_emalify.session.batch.size', 10))
        return super()._get_batch_size()
