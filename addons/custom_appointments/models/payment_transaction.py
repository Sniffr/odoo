from odoo import models, fields


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'
    
    appointment_id = fields.Many2one('custom.appointment', string='Appointment', compute='_compute_appointment_id', store=True)
    
    def _compute_appointment_id(self):
        for transaction in self:
            appointment = self.env['custom.appointment'].search([('payment_transaction_id', '=', transaction.id)], limit=1)
            transaction.appointment_id = appointment.id if appointment else False
