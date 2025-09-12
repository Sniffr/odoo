from odoo import models, fields, api


class StaffMember(models.Model):
    _name = 'custom.staff.member'
    _description = 'Staff Member for Appointments'
    _rec_name = 'name'

    name = fields.Char(string='Full Name', required=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', help='Link to HR Employee if available')
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
