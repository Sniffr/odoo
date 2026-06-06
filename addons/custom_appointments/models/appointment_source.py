from odoo import models, fields


class AppointmentSource(models.Model):
    _name = 'custom.appointment.source'
    _description = 'Appointment Source'
    _order = 'sequence, name'

    name = fields.Char(string='Source', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True)
