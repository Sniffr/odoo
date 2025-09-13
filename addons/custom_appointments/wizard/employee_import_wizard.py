from odoo import models, fields, api


class EmployeeImportWizard(models.TransientModel):
    _name = 'employee.import.wizard'
    _description = 'Import Employees as Staff Members'

    import_mode = fields.Selection([
        ('all', 'Import All Employees'),
        ('selected', 'Import Selected Employees'),
        ('missing', 'Import Only Missing Employees')
    ], string='Import Mode', default='missing', required=True)
    
    employee_ids = fields.Many2many('hr.employee', string='Employees to Import')
    branch_id = fields.Many2one('custom.branch', string='Default Branch', required=True,
                               help='Branch to assign to imported staff members')
    
    update_existing = fields.Boolean(string='Update Existing Staff', default=True,
                                   help='Update existing staff members with employee data')
    
    make_bookable = fields.Boolean(string='Make Bookable by Default', default=True,
                                 help='Set imported staff as bookable for appointments')
    
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        default_branch = self.env['custom.branch'].search([], limit=1)
        if default_branch:
            res['branch_id'] = default_branch.id
        return res
    
    @api.onchange('import_mode')
    def _onchange_import_mode(self):
        """Update employee selection based on import mode"""
        if self.import_mode == 'all':
            self.employee_ids = self.env['hr.employee'].search([])
        elif self.import_mode == 'missing':
            existing_employee_ids = self.env['custom.staff.member'].search([
                ('employee_id', '!=', False)
            ]).mapped('employee_id.id')
            missing_employees = self.env['hr.employee'].search([
                ('id', 'not in', existing_employee_ids)
            ])
            self.employee_ids = missing_employees
        else:
            self.employee_ids = False
    
    def action_import_employees(self):
        """Import selected employees as staff members"""
        if not self.employee_ids:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Warning',
                    'message': 'No employees selected for import.',
                    'type': 'warning',
                }
            }
        
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        for employee in self.employee_ids:
            existing_staff = self.env['custom.staff.member'].search([
                ('employee_id', '=', employee.id)
            ], limit=1)
            
            staff_vals = {
                'name': employee.name,
                'email': employee.work_email or employee.private_email or '',
                'phone': employee.work_phone or employee.mobile_phone or '',
                'employee_id': employee.id,
                'branch_id': self.branch_id.id,
                'specialization': employee.job_title or '',
                'is_bookable': self.make_bookable,
            }
            
            if existing_staff:
                if self.update_existing:
                    existing_staff.write(staff_vals)
                    updated_count += 1
                else:
                    skipped_count += 1
            else:
                self.env['custom.staff.member'].create(staff_vals)
                created_count += 1
        
        message = f"Import completed:\n• Created: {created_count}\n• Updated: {updated_count}\n• Skipped: {skipped_count}"
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Import Completed',
                'message': message,
                'type': 'success',
            }
        }
