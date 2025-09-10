from odoo import models, fields, api
from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import ValidationError,RedirectWarning, UserError
from datetime import datetime, timedelta
from ...models.eagle.eagle import EagleConnection
import logging
_logger = logging.getLogger(__name__)

class WizarPaymemt(models.Model):
    _name = "wizard.payment"
    _description = 'Wizard Payment'

    
    amount = fields.Float()
    sent_code = fields.Boolean()
    account_peppol_verification_code = fields.Char(string="Authorization Code")
    message = fields.Text()
    user_email = fields.Char()
    wizard_id = fields.Integer()
    payment_batch_id = fields.Many2one('payment.batch')

    def action_send(self):
        pass
        
        
    def action_validate(self):
        find_code = self.env['authorization.code'].sudo().search([('payment_batch_id','=',self.payment_batch_id.id),('code','=',self.account_peppol_verification_code)],order="id desc",limit=1)
        if not find_code:
            raise ValidationError("Invalid Code")
        else:
            create_date = find_code.create_date
            current_datetime = datetime.now()

            # Calculate the difference between the current datetime and the record's create date
            time_difference = current_datetime - create_date
            if time_difference >= timedelta(minutes=3):
                raise ValidationError("Expired Code")
        if self.payment_batch_id.state == 'draft':
            self.payment_batch_id.sudo().write({'state':'pending'})
        elif self.payment_batch_id.state == 'pending':
            self.payment_batch_id.sudo().write({'state':'pre_approved'})
        elif self.payment_batch_id.state == 'pre_approved':
            self.payment_batch_id.sudo().write({'state':'approved'})
            return self.payment_batch_id.eagle_payment_ids.sudo().make_payment()
            
class SingleWizardPaymemt(models.Model):
    _name = "single.wizard.payment"
    _description = 'Single Wizard Payment'

    
    amount = fields.Float()
    sent_code = fields.Boolean()
    account_peppol_verification_code = fields.Char(string="Authorization Code")
    message = fields.Text()
    user_email = fields.Char()
    wizard_id = fields.Integer()
    eagle_payment_id = fields.Many2one('eagle.payment')

    def action_send(self):
        pass
        
        
    def action_validate(self):
        find_code = self.env['authorization.code'].sudo().search([('eagle_payment_id','=',self.eagle_payment_id.id),('code','=',self.account_peppol_verification_code)],order="id desc",limit=1)
        if not find_code:
            raise ValidationError("Invalid Code")
        else:
            create_date = find_code.create_date
            current_datetime = datetime.now()

            # Calculate the difference between the current datetime and the record's create date
            time_difference = current_datetime - create_date
            if time_difference >= timedelta(minutes=3):
                raise ValidationError("Expired Code")
        if self.eagle_payment_id.state == 'approved':
            return self.eagle_payment_id.sudo().make_payment()
            