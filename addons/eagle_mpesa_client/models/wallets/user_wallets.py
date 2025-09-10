from odoo import fields, models, api, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from ...models.eagle.eagle import EagleConnection
import logging
_logger = logging.getLogger(__name__)


class UserWallet(models.Model):
    _name = "user.wallet"
    _description = "Partner Wallet"
    _inherit = ['mail.thread','mail.activity.mixin', 'image.mixin']
    

    # @api.model
    # def create(self, vals):
    #     if not self.env.user.has_group('eagle_mpesa_client.group_kpayment_accountant'):
    #         raise UserError(_("You don't have access to create wallets."))
    #     return super(UserWallet, self).create(vals)

    @api.constrains('user_id','company_id')
    def _check_user_id(self):
        for rec in self:
            if rec.user_id:
                other_wallets = self.env['user.wallet'].sudo().search([
                    ('user_id','=',rec.user_id.id),
                    ('id','!=',rec.id),
                    ('company_id','=',rec.company_id.id),   
                ])
                if other_wallets:
                    raise ValidationError("User already has a wallet under this company")

    @api.constrains('partner_id','company_id')
    def _check_partner_id(self):
        for rec in self:
            if rec.partner_id:
                other_wallets = self.env['user.wallet'].sudo().search([
                    ('partner_id','!=',False),
                    ('id','!=',rec.id),
                    ('company_id','=',rec.company_id.id),   
                ])
                if other_wallets:
                    raise ValidationError("Company already has partner")


    name = fields.Char(readonly=True, index='trigram',default=lambda self: _('New'),copy=False)
    user_id = fields.Many2one('res.users')
    partner_id = fields.Many2one('res.partner')
    wallet_balance = fields.Monetary(store=True)
    amount_sent = fields.Monetary(store=True)
    amount_received = fields.Monetary(store=True)
    amount_charged = fields.Monetary(store=True)
    active = fields.Boolean(tracking=True,default=True)

    wallet_transaction_ids = fields.One2many('wallet.transaction','wallet_id')
    company_id = fields.Many2one('res.company', string='Company', required=True,
        default=lambda self: self.env.company)    
    currency_id = fields.Many2one(related="company_id.currency_id",store=True)
    company_wallet = fields.Boolean(compute="_compute_company_wallet",store=True)
    eagle_status = fields.Selection(selection=[
        ('pending','Pending'),
        ('active', 'Active'),
    ],default='pending', tracking=True)
    
    @api.depends('user_id','partner_id','name')
    def _compute_display_name(self):
        for rec in self:
            if rec.partner_id:
                rec.display_name = f"{rec.partner_id.name} - {rec.name}"
            elif rec.user_id:
                rec.display_name = f"{rec.user_id.name} - {rec.name}"
            else:
                rec.display_name = f"{rec.name}"
    @api.depends('partner_id')
    def _compute_company_wallet(self):
        for rec in self:
            rec.company_wallet = False
            # if rec.partner_id.company_type == 'company':
            find_company = self.env['res.company'].sudo().search([('partner_id','=',rec.partner_id.id)])
            if find_company:
                rec.company_wallet = True

  

    
    def activate_on_eagle(self):
        try:
           
            vals_dict = {
                'wallet_name':self.name,
                'partner_id':self.partner_id.id if self.partner_id else False,
                'partner_name':self.partner_id.name if self.partner_id else False,
                'user_id':self.user_id.id if self.user_id else False,
                'user_name':self.user_id.name if self.user_id else False,
                'user_email':f"{self.user_id.login}@bypass" if self.user_id else False,
                'company_wallet':self.company_wallet,
            }
            
            eagle_connection = EagleConnection(model='eagle.connection',method='get_create_wallet',values=[vals_dict])
            response = eagle_connection.get_response(self.company_id)
            _logger.info(response)
           

            if response.get("success") and response.get('wallet'):
                wallet = response.get('wallet')
                if self.eagle_status != 'active':
                    self.eagle_status = 'active'
                self.name = wallet.get('wallet_name')
                self.wallet_balance = wallet.get('wallet_balance')
                self.wallet_transaction_ids.sudo().unlink()
                for transaction in wallet.get('transactions'):
                    self.env['wallet.transaction'].sudo().create([{
                        'transaction_type':transaction.get('transaction_type'),
                        'amount_received':transaction.get('amount_received'),
                        'amount_sent':transaction.get('amount_sent'),
                        'charged_fees':transaction.get('charged_fees'),
                        'phone_number':transaction.get('phone_number'),
                        'date':transaction.get('date'),
                        'comment':transaction.get('comment'),
                        'sender':transaction.get('sender'),
                        'transaction_id':transaction.get('transaction_id'),
                        'transaction_time':transaction.get('transaction_time'),
                        'wallet_id':self.id,
                        
                    }])
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
        
    def allocate_funds(self):
        self.activate_on_eagle()
        if self.wallet_balance < 10:
            raise ValidationError("You have less than 10 KES.")
        wizard = self.env['wizard.wallet'].sudo().create({
            'sender_wallet':self.id,
        })
        action = {
            'name': 'Allocate Funds',
            'res_model': 'wizard.wallet',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': self.env.ref('eagle_mpesa_client.wizard_wallet_form').id,
            'res_id': wizard.id,
            'target': 'new',
        }

        return action

    def update_payment_provider_keys(self,vals):
        pass

    def send_to_other_channels(self,vals_dict):
        pass