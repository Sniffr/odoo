from odoo import models, fields, api


class AppointmentSettings(models.Model):
    _name = 'custom.appointment.settings'
    _description = 'Appointment Communication Settings'
    _rec_name = 'id'

    # Master toggle
    send_followup_messages = fields.Boolean(
        string='Send Follow-up Messages',
        default=False,
        help='Enable or disable follow-up messages to customers after their appointment'
    )

    # Channel selection
    followup_channel = fields.Selection([
        ('sms', 'SMS Only'),
        ('email', 'Email Only'),
        ('both', 'Both SMS and Email')
    ], string='Communication Channel', default='both', required=True,
       help='Choose which channel(s) to use for follow-up messages')

    # Timing settings
    followup_start_days = fields.Integer(
        string='Start After (Days)',
        default=14,
        help='Number of days after appointment completion to send the first follow-up message'
    )

    followup_repeat_interval = fields.Integer(
        string='Repeat Every (Days)',
        default=7,
        help='Number of days between subsequent follow-up messages'
    )

    # Follow-up limits
    max_followup_count = fields.Integer(
        string='Maximum Follow-ups',
        default=3,
        help='Maximum number of follow-up messages to send per appointment'
    )

    followup_until_rebooked = fields.Boolean(
        string='Follow-up Until Rebooked',
        default=False,
        help='Keep sending follow-up messages until the customer books a new appointment (overrides maximum count)'
    )

    # Message templates
    followup_email_subject = fields.Char(
        string='Email Subject',
        default='We Miss You! Book Your Next Session',
        help='Subject line for follow-up emails'
    )

    followup_email_template = fields.Text(
        string='Email Message Template',
        help='Email template with placeholders: {customer_name}, {service_name}, {branch_name}, {booking_link}'
    )

    followup_sms_template = fields.Text(
        string='SMS Message Template',
        default='Hi {customer_name}! We hope you enjoyed your {service_name}. Ready for your next session? Book now: {booking_link}',
        help='SMS template with placeholders: {customer_name}, {service_name}, {branch_name}, {booking_link}'
    )

    @api.model
    def get_settings(self):
        """Get or create the singleton settings record"""
        settings = self.search([], limit=1)
        if not settings:
            settings = self.create({
                'followup_start_days': 14,
                'followup_repeat_interval': 7,
                'max_followup_count': 3,
                'followup_channel': 'both',
                'followup_email_subject': 'We Miss You! Book Your Next Session',
                'followup_sms_template': 'Hi {customer_name}! We hope you enjoyed your {service_name}. Ready for your next session? Book now: {booking_link}',
            })
        return settings

    def write(self, vals):
        """Ensure only one settings record exists"""
        return super(AppointmentSettings, self).write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        """Ensure only one settings record exists"""
        existing = self.search([], limit=1)
        if existing:
            existing.write(vals_list[0] if vals_list else {})
            return existing
        return super(AppointmentSettings, self).create(vals_list)
