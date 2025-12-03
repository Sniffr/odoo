from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Appointment Follow-up Configuration
    appointment_followup_enabled = fields.Boolean(
        related='company_id.appointment_followup_enabled',
        readonly=False,
        string='Enable Appointment Follow-ups'
    )
    appointment_followup_delay_hours = fields.Float(
        related='company_id.appointment_followup_delay_hours',
        readonly=False,
        string='Follow-up Delay (Hours)'
    )
    appointment_followup_channel = fields.Selection(
        related='company_id.appointment_followup_channel',
        readonly=False,
        string='Follow-up Channel'
    )
