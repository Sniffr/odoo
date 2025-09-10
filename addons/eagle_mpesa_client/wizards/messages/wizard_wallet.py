from odoo import models, fields, api
from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import ValidationError,RedirectWarning, UserError
from datetime import datetime, timedelta
from ...models.eagle.eagle import EagleConnection
import logging
_logger = logging.getLogger(__name__)

class WizardWallet(models.Model):
    _name = "wizard.wallet"
    _description = 'Wizard Wallet'

    
    amount = fields.Float()
    sent_code = fields.Boolean()
    account_peppol_verification_code = fields.Char(string="Authorization Code")
    sender_wallet = fields.Many2one('user.wallet')
    receiver_wallet = fields.Many2one('user.wallet')
    message = fields.Text()
    user_email = fields.Char()
    wizard_id = fields.Integer()
    funds_request_id = fields.Many2one('funds.request')

    def action_send(self):
        if self.amount < 10:
            raise ValidationError("Amount cannot be less than 10.")
        try:
            print(self.sender_wallet.name)
            print(self.sender_wallet.name)
            print(self.sender_wallet.name)
            vals_dict = {
                'sender_wallet':self.sender_wallet.name,
                'receiver_wallet':self.receiver_wallet.name,
                'amount':self.amount,
                # 'user_email':self.env.user.email,
                'user_email':self.user_email,
            }
            
            eagle_connection = EagleConnection(model='eagle.connection',method='create_wallet_transfer',values=[vals_dict])
            response = eagle_connection.get_response(self.sender_wallet.company_id)
            _logger.info(response)
           

            if response.get("success") and response.get('wizard_id'):
                self.sent_code = True
                self.wizard_id = response.get('wizard_id')
                self.message = f"An authorization code has been sent to {self.user_email}\nKindly enter the code and approve this funds allocation"
                action = {
                    'name': 'Allocate Funds',
                    'res_model': 'wizard.wallet',
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'view_id': self.env.ref('eagle_mpesa_client.wizard_wallet_form').id,
                    'res_id': self.id,
                    'target': 'new',
                }

                return action
            elif response.get('message'):
                raise ValidationError(response.get('message'))
            else:
                print("")
                print("")
                print(response)
                raise ValidationError("An unexpected error occured! Kindly contact administrator.")

        except Exception as e:
            raise ValidationError(e)

        print(response)
        
        
    def action_validate(self):
        try:
            if self.funds_request_id and self.funds_request_id.state == 'confirmed':
                find_code = self.env['authorization.code'].sudo().search([('funds_request_id','=',self.funds_request_id.id),('code','=',self.account_peppol_verification_code)],order="id desc",limit=1)
                if not find_code:
                    raise ValidationError("Invalid Code")
                else:
                    create_date = find_code.create_date
                    current_datetime = datetime.now()

                    # Calculate the difference between the current datetime and the record's create date
                    time_difference = current_datetime - create_date
                    if time_difference >= timedelta(minutes=3):
                        raise ValidationError("Expired Code")
                    self.funds_request_id.sudo().write({'state':'pre_approved','preapprover_id':self.env.user.id})
                    try:
                        self.funds_request_id.sudo().send_mail_to_approvers()
                    except Exception as e:
                        print(e)
                        print(e)
                    return 1
           
            vals_dict = {
                'wizard_id':self.wizard_id,
                'code':self.account_peppol_verification_code,
            }
            
            eagle_connection = EagleConnection(model='eagle.connection',method='validate_wallet_transfer',values=[vals_dict])
            response = eagle_connection.get_response(self.sender_wallet.company_id)
            _logger.info(response)
           

            if response.get("success") and response.get('wizard_id'):
                self.sender_wallet.activate_on_eagle()
                self.receiver_wallet.activate_on_eagle()
                if self.funds_request_id:
                    self.funds_request_id.sudo().write({'state':'approved','approver_id':self.env.user.id})
                    try:
                        self.funds_request_id.sudo().send_mail_to_approvers()
                    except Exception as e:
                        print(e)
                        print(e)
                message_id = self.env['message.wizard'].create(
                        {'message': _("Funds Successfully Allocated. Kindly refresh to confirm")})
                return {
                    'name': _('Successfull'),
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'res_model': 'message.wizard',
                    # pass the id
                    'res_id': message_id.id,
                    'target': 'new'
                }
            elif response.get('message'):
                raise ValidationError(response.get('message'))
            else:
                print("")
                print("")
                print(response)
                raise ValidationError("An unexpected error occured! Kindly contact administrator.")

        except Exception as e:
            raise ValidationError(e)

        print(response)

    