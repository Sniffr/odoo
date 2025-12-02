from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    appointment_ids = fields.One2many('custom.appointment', 'partner_id', string='Appointments')
    appointment_count = fields.Integer(string='Appointment Count', compute='_compute_appointment_count', store=True)
    total_paid_amount = fields.Monetary(string='Total Paid', compute='_compute_total_paid_amount', store=True, currency_field='currency_id')
    payment_transaction_ids = fields.One2many('payment.transaction', 'partner_id', string='Payment Transactions', domain=[('appointment_id', '!=', False)])
    
    @api.depends('appointment_ids')
    def _compute_appointment_count(self):
        for partner in self:
            partner.appointment_count = len(partner.appointment_ids)
    
    @api.depends('appointment_ids.paid_amount', 'appointment_ids.payment_status')
    def _compute_total_paid_amount(self):
        for partner in self:
            paid_appointments = partner.appointment_ids.filtered(lambda a: a.payment_status == 'paid')
            partner.total_paid_amount = sum(paid_appointments.mapped('paid_amount'))
    
    def action_view_appointments(self):
        self.ensure_one()
        return {
            'name': 'Appointments',
            'type': 'ir.actions.act_window',
            'res_model': 'custom.appointment',
            'view_mode': 'list,form,calendar',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id},
        }
    
    def action_view_payments(self):
        self.ensure_one()
        return {
            'name': 'Payment Transactions',
            'type': 'ir.actions.act_window',
            'res_model': 'payment.transaction',
            'view_mode': 'list,form',
            'domain': [('partner_id', '=', self.id), ('appointment_id', '!=', False)],
            'context': {'default_partner_id': self.id},
        }
