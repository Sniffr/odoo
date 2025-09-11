from odoo import models, fields, api
from odoo.exceptions import ValidationError

class StaffMember(models.Model):
    _inherit = 'res.partner'
    
    is_bookable = fields.Boolean(
        string='Bookable Staff',
        default=False,
        help='Mark this person as available for appointment booking on the website'
    )
    
    specialization = fields.Text(
        string='Specialization',
        help='Area of expertise or specialization for this staff member'
    )
    
    available_hours = fields.Text(
        string='Available Hours',
        help='General availability information for this staff member'
    )
    
    website_url = fields.Char(
        string='Website URL',
        compute='_compute_website_url',
        help='URL to view this staff member profile on the website'
    )
    
    @api.depends('is_bookable')
    def _compute_website_url(self):
        for record in self:
            if record.is_bookable:
                record.website_url = f'/appointments/staff/{record.id}' if record.id else False
            else:
                record.website_url = False
    
    @api.constrains('is_bookable', 'name')
    def _check_bookable_staff(self):
        for record in self:
            if record.is_bookable and not record.name:
                raise ValidationError('Bookable staff members must have a name!')
    
    def action_make_bookable(self):
        self.is_bookable = True
    
    def action_make_unbookable(self):
        self.is_bookable = False
