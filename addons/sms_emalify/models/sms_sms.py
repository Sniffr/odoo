# -*- coding: utf-8 -*-
import logging
from collections import defaultdict

from odoo import fields, models, api

_logger = logging.getLogger(__name__)


class SmsSms(models.Model):
    _inherit = 'sms.sms'

    record_company_id = fields.Many2one(
        'res.company',
        string='Company',
        ondelete='set null',
    )
    failure_type = fields.Selection(
        selection_add=[
            ('emalify_auth', 'Emalify Authentication Error'),
            ('emalify_invalid_number', 'Invalid Number Format'),
            ('emalify_server_error', 'Emalify Server Error'),
        ],
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Store company on SMS record for provider routing."""
        for vals in vals_list:
            if not vals.get('record_company_id'):
                vals['record_company_id'] = self.env.company.id
        return super().create(vals_list)

    def _split_by_api(self):
        """Override to handle Emalify provider selection based on company."""
        _logger.info("Emalify _split_by_api called for SMS ids: %s", self.ids)
        
        sms_by_company = defaultdict(lambda: self.env['sms.sms'])
        todo_via_super = self.browse()
        
        for sms in self:
            company = sms._get_sms_company()
            sms_by_company[company] += sms
        
        for company, company_sms in sms_by_company.items():
            _logger.info(
                "Emalify routing: company=%s (id=%s), sms_provider=%s, sms_ids=%s",
                company.name, company.id, company.sms_provider, company_sms.ids
            )
            if company.sms_provider == 'emalify':
                _logger.info("Routing SMS via Emalify for company %s", company.name)
                sms_api = company._get_sms_api_class()(self.env)
                sms_api._set_company(company)
                yield sms_api, company_sms
            else:
                _logger.info("Routing SMS via default (IAP) for company %s", company.name)
                todo_via_super += company_sms
        
        if todo_via_super:
            yield from super(SmsSms, todo_via_super)._split_by_api()

    def _get_sms_company(self):
        """Get the company for this SMS record."""
        return (
            self.mail_message_id.record_company_id 
            or self.record_company_id 
            or super()._get_sms_company()
        )
