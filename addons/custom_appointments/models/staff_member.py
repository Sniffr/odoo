from odoo import models, fields, api


class StaffMember(models.Model):
    _name = 'custom.staff.member'
    _description = 'Staff Member for Appointments'
    _rec_name = 'name'

    name = fields.Char(string='Full Name', required=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', help='Link to HR Employee if available', ondelete='cascade')
    email = fields.Char(string='Email')
    phone = fields.Char(string='Phone')
    branch_id = fields.Many2one('custom.branch', string='Branch', required=True)
    
    is_bookable = fields.Boolean(string='Available for Booking', default=True)
    specialization = fields.Char(string='Specialization/Role')
    hourly_rate = fields.Float(string='Hourly Rate', help='Rate per hour for services')
    
    monday_available = fields.Boolean(string='Monday', default=True)
    tuesday_available = fields.Boolean(string='Tuesday', default=True)
    wednesday_available = fields.Boolean(string='Wednesday', default=True)
    thursday_available = fields.Boolean(string='Thursday', default=True)
    friday_available = fields.Boolean(string='Friday', default=True)
    saturday_available = fields.Boolean(string='Saturday', default=False)
    sunday_available = fields.Boolean(string='Sunday', default=False)
    
    start_time = fields.Float(string='Start Time', default=9.0, help='Daily start time (24h format)')
    end_time = fields.Float(string='End Time', default=17.0, help='Daily end time (24h format)')
    
    active = fields.Boolean(string='Active', default=True)
    notes = fields.Text(string='Notes')
    
    @api.depends('name', 'specialization')
    def _compute_display_name(self):
        for record in self:
            if record.specialization:
                record.display_name = f"{record.name} ({record.specialization})"
            else:
                record.display_name = record.name
    
    display_name = fields.Char(compute='_compute_display_name', store=True)
    
    @api.model
    def sync_from_employees(self):
        """Sync staff members from HR employees"""
        employees = self.env['hr.employee'].search([])
        created_count = 0
        updated_count = 0
        
        for employee in employees:
            existing_staff = self.search([('employee_id', '=', employee.id)], limit=1)
            
            default_branch = self.env['custom.branch'].search([], limit=1)
            if not default_branch:
                continue
                
            staff_vals = {
                'name': employee.name,
                'email': employee.work_email or employee.private_email or '',
                'phone': employee.work_phone or employee.mobile_phone or '',
                'employee_id': employee.id,
                'branch_id': default_branch.id,
                'specialization': employee.job_title or '',
                'is_bookable': True,  # Default to bookable, can be changed manually
            }
            
            if existing_staff:
                existing_staff.write(staff_vals)
                updated_count += 1
            else:
                self.create(staff_vals)
                created_count += 1
                
        return {
            'created': created_count,
            'updated': updated_count,
            'total_employees': len(employees)
        }
    
    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        """Auto-populate fields when employee is selected"""
        if self.employee_id:
            self.name = self.employee_id.name
            self.email = self.employee_id.work_email or self.employee_id.private_email or ''
            self.phone = self.employee_id.work_phone or self.employee_id.mobile_phone or ''
            self.specialization = self.employee_id.job_title or ''
    
    def action_sync_from_employee(self):
        """Action to sync individual staff member from linked employee"""
        if self.employee_id:
            self.write({
                'name': self.employee_id.name,
                'email': self.employee_id.work_email or self.employee_id.private_email or '',
                'phone': self.employee_id.work_phone or self.employee_id.mobile_phone or '',
                'specialization': self.employee_id.job_title or '',
            })
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Success',
                    'message': f'Staff member {self.name} synced from employee data.',
                    'type': 'success',
                }
            }
