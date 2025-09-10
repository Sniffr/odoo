from odoo import models, fields, api

class RejectPayment(models.TransientModel):
    _name = 'reject.payment'
    _description="Reject Payment"

    payment_batch_id = fields.Many2one('payment.batch')
    cancel_reason_id = fields.Many2one('cancel.reason',string="Reason")

    def reject(self):
        self.payment_batch_id.cancel_reason_id = self.cancel_reason_id.id
        self.payment_batch_id.state = 'cancelled'
        for payment in self.payment_batch_id.eagle_payment_ids:
            if payment.state != 'done':
                payment.state = 'cancel'
                payment.fail_reason = self.cancel_reason_id.name

class CancelPayment(models.TransientModel):
    _name = 'cancel.payment'
    _description="Cancel Payment"

    eagle_payment_id = fields.Many2one('eagle.payment')
    cancel_reason_id = fields.Many2one('cancel.reason',string="Reason")

    def reject(self):
        self.eagle_payment_id.fail_reason = self.cancel_reason_id.name
        self.eagle_payment_id.state = 'cancel'
       

class RejectFundsRequest(models.TransientModel):
    _name = 'reject.funds.request'
    _description="Reject Funds Request"

    funds_request_id = fields.Many2one('funds.request')
    cancel_reason_id = fields.Many2one('cancel.reason',string="Reason")

    def reject(self):
        self.funds_request_id.reason_for_reject_id = self.cancel_reason_id.id
        self.funds_request_id.state = 'rejected'
       