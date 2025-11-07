from odoo import models, fields, api


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'
    
    appointment_id = fields.Many2one('custom.appointment', string='Appointment', compute='_compute_appointment_id', store=True)
    
    @api.depends('id')
    def _compute_appointment_id(self):
        for transaction in self:
            if transaction.id:
                appointment = self.env['custom.appointment'].search([('payment_transaction_id', '=', transaction.id)], limit=1)
                transaction.appointment_id = appointment.id if appointment else False
            else:
                transaction.appointment_id = False
