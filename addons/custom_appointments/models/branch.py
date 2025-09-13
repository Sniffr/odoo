from odoo import models, fields, api


class Branch(models.Model):
    _name = 'custom.branch'
    _description = 'Company Branch'
    _rec_name = 'name'

    name = fields.Char(string='Branch Name', required=True)
    company_id = fields.Many2one('res.company', string='Company', help='Link to Company if available', ondelete='cascade')
    code = fields.Char(string='Branch Code', help='Short code for the branch')
    
    street = fields.Char(string='Street')
    street2 = fields.Char(string='Street 2')
    city = fields.Char(string='City')
    state_id = fields.Many2one('res.country.state', string='State')
    country_id = fields.Many2one('res.country', string='Country')
    zip = fields.Char(string='ZIP Code')
    
    phone = fields.Char(string='Phone')
    email = fields.Char(string='Email')
    website = fields.Char(string='Website')
    
    is_main_branch = fields.Boolean(string='Main Branch', default=False)
    active = fields.Boolean(string='Active', default=True)
    
    staff_member_ids = fields.One2many('custom.staff.member', 'branch_id', string='Staff Members')
    staff_count = fields.Integer(string='Staff Count', compute='_compute_staff_count')
    
    monday_open = fields.Float(string='Monday Open', default=9.0)
    monday_close = fields.Float(string='Monday Close', default=17.0)
    tuesday_open = fields.Float(string='Tuesday Open', default=9.0)
    tuesday_close = fields.Float(string='Tuesday Close', default=17.0)
    wednesday_open = fields.Float(string='Wednesday Open', default=9.0)
    wednesday_close = fields.Float(string='Wednesday Close', default=17.0)
    thursday_open = fields.Float(string='Thursday Open', default=9.0)
    thursday_close = fields.Float(string='Thursday Close', default=17.0)
    friday_open = fields.Float(string='Friday Open', default=9.0)
    friday_close = fields.Float(string='Friday Close', default=17.0)
    saturday_open = fields.Float(string='Saturday Open', default=0.0)
    saturday_close = fields.Float(string='Saturday Close', default=0.0)
    sunday_open = fields.Float(string='Sunday Open', default=0.0)
    sunday_close = fields.Float(string='Sunday Close', default=0.0)
    
    notes = fields.Text(string='Notes')
    
    @api.depends('staff_member_ids')
    def _compute_staff_count(self):
        for record in self:
            record.staff_count = len(record.staff_member_ids)
    
    def action_view_staff(self):
        """Action to view staff members for this branch"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Staff Members',
            'res_model': 'custom.staff.member',
            'view_mode': 'list,form',
            'domain': [('branch_id', '=', self.id)],
            'context': {'default_branch_id': self.id},
        }
    
    @api.model
    def create(self, vals):
        if vals.get('is_main_branch'):
            existing_main = self.search([('is_main_branch', '=', True)])
            existing_main.write({'is_main_branch': False})
        return super().create(vals)
    
    def write(self, vals):
        if vals.get('is_main_branch'):
            other_branches = self.search([('id', 'not in', self.ids), ('is_main_branch', '=', True)])
            other_branches.write({'is_main_branch': False})
        return super().write(vals)
    
    @api.onchange('company_id')
    def _onchange_company_id(self):
        """Auto-populate fields when company is selected"""
        if self.company_id:
            self.name = self.company_id.name
            self.street = self.company_id.street or ''
            self.street2 = self.company_id.street2 or ''
            self.city = self.company_id.city or ''
            self.state_id = self.company_id.state_id
            self.country_id = self.company_id.country_id
            self.zip = self.company_id.zip or ''
            self.phone = self.company_id.phone or ''
            self.email = self.company_id.email or ''
            self.website = self.company_id.website or ''

    def action_sync_from_company(self):
        """Action to sync individual branch from linked company"""
        if self.company_id:
            self.write({
                'name': self.company_id.name,
                'street': self.company_id.street or '',
                'street2': self.company_id.street2 or '',
                'city': self.company_id.city or '',
                'state_id': self.company_id.state_id.id if self.company_id.state_id else False,
                'country_id': self.company_id.country_id.id if self.company_id.country_id else False,
                'zip': self.company_id.zip or '',
                'phone': self.company_id.phone or '',
                'email': self.company_id.email or '',
                'website': self.company_id.website or '',
            })
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Success',
                    'message': f'Branch {self.name} synced from company data.',
                    'type': 'success',
                }
            }
