from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    # Appointment Auto-Completion Configuration
    appointment_autocomplete_enabled = fields.Boolean(
        string='Auto-Complete Appointments',
        default=True,
        help='Automatically mark appointments as completed after their end time passes.'
    )
    appointment_autocomplete_grace_minutes = fields.Integer(
        string='Auto-Complete Grace Period (Minutes)',
        default=30,
        help='Minutes to wait after appointment end time before auto-completing. '
             'This gives staff time to manually complete appointments.'
    )

    # Appointment Follow-up Configuration
    appointment_followup_enabled = fields.Boolean(
        string='Enable Appointment Follow-ups',
        default=True,
        help='Enable automatic follow-up messages after appointments are completed.'
    )
    appointment_followup_delay_hours = fields.Float(
        string='Follow-up Delay (Hours)',
        default=2.0,
        help='Number of hours after appointment end time to send the follow-up message. '
             'Set to 0 for immediate follow-up on completion.'
    )
    appointment_followup_channel = fields.Selection([
        ('email', 'Email Only'),
        ('sms', 'SMS Only'),
        ('both', 'Email and SMS')
    ], string='Follow-up Channel', default='both',
       help='Choose how to send follow-up messages to customers.')
