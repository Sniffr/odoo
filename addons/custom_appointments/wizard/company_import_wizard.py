from odoo import models, fields, api


class CompanyImportWizard(models.TransientModel):
    _name = 'company.import.wizard'
    _description = 'Import Companies as Branches'

    import_mode = fields.Selection([
        ('all', 'Import All Companies'),
        ('selected', 'Import Selected Companies'),
        ('missing', 'Import Missing Companies Only')
    ], string='Import Mode', default='missing', required=True)
    
    company_ids = fields.Many2many('res.company', string='Companies to Import')
    update_existing = fields.Boolean(string='Update Existing Branches', default=False,
                                   help='Update existing branches with company data')
    set_main_branch = fields.Boolean(string='Set First as Main Branch', default=True,
                                   help='Set the first imported branch as main branch')
    
    @api.onchange('import_mode')
    def _onchange_import_mode(self):
        if self.import_mode == 'all':
            self.company_ids = [(5, 0, 0)]
        elif self.import_mode == 'selected':
            pass
        elif self.import_mode == 'missing':
            existing_company_ids = self.env['custom.branch'].search([('company_id', '!=', False)]).mapped('company_id.id')
            missing_companies = self.env['res.company'].search([('id', 'not in', existing_company_ids)])
            self.company_ids = [(6, 0, missing_companies.ids)]

    def action_import_companies(self):
        """Import companies as branches"""
        if self.import_mode == 'all':
            companies = self.env['res.company'].search([])
        elif self.import_mode == 'selected':
            companies = self.company_ids
        else:
            existing_company_ids = self.env['custom.branch'].search([('company_id', '!=', False)]).mapped('company_id.id')
            companies = self.env['res.company'].search([('id', 'not in', existing_company_ids)])

        created_count = 0
        updated_count = 0
        first_branch = True

        for company in companies:
            existing_branch = self.env['custom.branch'].search([('company_id', '=', company.id)], limit=1)
            
            branch_vals = {
                'name': company.name,
                'company_id': company.id,
                'street': company.street or '',
                'street2': company.street2 or '',
                'city': company.city or '',
                'state_id': company.state_id.id if company.state_id else False,
                'country_id': company.country_id.id if company.country_id else False,
                'zip': company.zip or '',
                'phone': company.phone or '',
                'email': company.email or '',
                'website': company.website or '',
                'code': company.name[:4].upper() if company.name else 'COMP',
                'is_main_branch': first_branch and self.set_main_branch,
            }
            
            if existing_branch:
                if self.update_existing:
                    existing_branch.write(branch_vals)
                    updated_count += 1
            else:
                self.env['custom.branch'].create(branch_vals)
                created_count += 1
                first_branch = False

        message = f"Import completed: {created_count} branches created"
        if updated_count > 0:
            message += f", {updated_count} branches updated"
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Import Completed',
                'message': message,
                'type': 'success',
            }
        }
