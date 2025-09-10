from odoo import models, fields, api

class MessageWizard(models.TransientModel):
    _name = 'message.wizard'
    _description='For Pop Up Messages'

    message = fields.Text('Message', required=True)
    trigger_cron_id = fields.Many2one('ir.cron.trigger')

  
    def action_ok(self):
        """ close wizard"""
        return {'type': 'ir.actions.act_window_close'}
        