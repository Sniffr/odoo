from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = 'account.move'
    
    appointment_id = fields.Many2one('custom.appointment', string='Appointment', compute='_compute_appointment_id', store=True)
    
    @api.depends('invoice_line_ids')
    def _compute_appointment_id(self):
        for move in self:
            appointment = self.env['custom.appointment'].search([('invoice_id', '=', move.id)], limit=1)
            move.appointment_id = appointment.id if appointment else False
    
    def action_view_appointment(self):
        self.ensure_one()
        if not self.appointment_id:
            return {}
        return {
            'name': 'Appointment',
            'type': 'ir.actions.act_window',
            'res_model': 'custom.appointment',
            'view_mode': 'form',
            'res_id': self.appointment_id.id,
        }
