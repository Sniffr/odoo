import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class PesaPalIPNLog(models.Model):
    _name = 'pesapal.ipn.log'
    _description = 'PesaPal IPN Notification Log'
    _order = 'create_date desc'
    _rec_name = 'tracking_id'

    tracking_id = fields.Char(
        string='Order Tracking ID',
        required=True,
        index=True,
        help='PesaPal order tracking ID'
    )
    merchant_reference = fields.Char(
        string='Merchant Reference',
        index=True,
        help='Merchant reference for the transaction'
    )
    status_code = fields.Integer(
        string='Status Code',
        help='Payment status code from PesaPal'
    )
    status_description = fields.Char(
        string='Status Description',
        help='Payment status description from PesaPal'
    )
    transaction_id = fields.Many2one(
        'payment.transaction',
        string='Payment Transaction',
        ondelete='set null',
        help='Related payment transaction'
    )
    appointment_id = fields.Many2one(
        'custom.appointment',
        string='Appointment',
        ondelete='set null',
        help='Related appointment'
    )
    processed = fields.Boolean(
        string='Processed',
        default=False,
        help='Whether this IPN has been processed'
    )
    processed_date = fields.Datetime(
        string='Processed Date',
        help='When this IPN was processed'
    )
    error_message = fields.Text(
        string='Error Message',
        help='Error message if processing failed'
    )
    raw_data = fields.Text(
        string='Raw Data',
        help='Raw IPN data received from PesaPal'
    )

    _sql_constraints = [
        ('tracking_id_unique', 'UNIQUE(tracking_id, create_date)', 
         'An IPN log with this tracking ID and timestamp already exists!')
    ]

    @api.model
    def log_ipn(self, tracking_id, merchant_ref, status_code, status_description, raw_data=None):
        """Log an IPN notification"""
        return self.create({
            'tracking_id': tracking_id,
            'merchant_reference': merchant_ref,
            'status_code': status_code,
            'status_description': status_description,
            'raw_data': str(raw_data) if raw_data else None,
        })

    def mark_processed(self, transaction=None, appointment=None, error=None):
        """Mark IPN as processed"""
        self.ensure_one()
        vals = {
            'processed': True,
            'processed_date': fields.Datetime.now(),
        }
        if transaction:
            vals['transaction_id'] = transaction.id
        if appointment:
            vals['appointment_id'] = appointment.id
        if error:
            vals['error_message'] = error
        self.write(vals)
