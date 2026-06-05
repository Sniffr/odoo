from odoo import models, fields, api
from datetime import timedelta
import secrets
import logging

_logger = logging.getLogger(__name__)


class AppointmentFeedback(models.Model):
    _name = 'custom.appointment.feedback'
    _description = 'Customer Appointment Feedback'
    _order = 'create_date desc'

    appointment_id = fields.Many2one(
        'custom.appointment', string='Appointment',
        required=True, ondelete='cascade', index=True)
    partner_id = fields.Many2one('res.partner', string='Customer')
    customer_name = fields.Char(string='Customer Name')
    customer_email = fields.Char(string='Customer Email')
    customer_phone = fields.Char(string='Customer Phone')
    staff_member_id = fields.Many2one('custom.staff.member', string='Staff Member')
    service_id = fields.Many2one('company.service', string='Service')
    branch_id = fields.Many2one('custom.branch', string='Branch')

    access_token = fields.Char(string='Access Token', index=True, copy=False)
    state = fields.Selection([
        ('pending', 'Pending'),
        ('submitted', 'Submitted'),
        ('expired', 'Expired'),
    ], string='Status', default='pending', required=True, index=True)

    request_count = fields.Integer(string='Requests Sent', default=0)
    last_request_date = fields.Datetime(string='Last Request Sent')
    submitted_date = fields.Datetime(string='Submitted On')

    # Curated answer fields (1-5 ratings: 0 = unanswered)
    staff_rating = fields.Integer(string='Staff Rating')
    service_rating = fields.Integer(string='Service Rating')
    recommend_score = fields.Selection(
        [(str(n), str(n)) for n in range(0, 11)],
        string='Recommend Score (NPS)')
    cleanliness_rating = fields.Integer(string='Cleanliness Rating')
    comfort_rating = fields.Integer(string='Comfort Rating')
    value_rating = fields.Integer(string='Value Rating')
    comments = fields.Text(string='Comments')

    reward_promo_id = fields.Many2one('custom.appointment.promo', string='Reward Promo Code')

    _sql_constraints = [
        ('appointment_unique', 'unique(appointment_id)',
         'Feedback already exists for this appointment.'),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('access_token'):
                vals['access_token'] = secrets.token_urlsafe(24)
        return super().create(vals_list)

    @api.model
    def _create_for_appointment(self, appointment):
        """Create a pending feedback record copying appointment data."""
        return self.create({
            'appointment_id': appointment.id,
            'partner_id': appointment.partner_id.id,
            'customer_name': appointment.customer_name,
            'customer_email': appointment.customer_email,
            'customer_phone': appointment.customer_phone,
            'staff_member_id': appointment.staff_member_id.id,
            'service_id': appointment.service_id.id,
            'branch_id': appointment.branch_id.id,
        })

    @api.model
    def _backfill_feedback_records(self):
        """Create pending feedback records for completed appointments missing one."""
        Appointment = self.env['custom.appointment']
        completed = Appointment.search([
            ('state', '=', 'completed'),
            ('completed_date', '!=', False),
        ])
        if not completed:
            return
        existing = self.search([('appointment_id', 'in', completed.ids)])
        existing_appt_ids = set(existing.mapped('appointment_id').ids)
        for appt in completed:
            if appt.id not in existing_appt_ids:
                self._create_for_appointment(appt)

    @api.model
    def cron_send_feedback_requests(self):
        """Cron entrypoint: backfill records, then send any due feedback requests."""
        settings = self.env['custom.appointment.settings'].get_settings()
        if not settings.enable_feedback_requests:
            return
        self._backfill_feedback_records()
        self._send_due_requests(settings)

    @api.model
    def _send_due_requests(self, settings):
        """Send feedback requests that are due. Implemented in Task 5."""
        return
