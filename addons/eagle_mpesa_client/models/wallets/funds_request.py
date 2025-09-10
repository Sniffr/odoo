from odoo import fields, models, api, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from ...models.eagle.eagle import EagleConnection
import logging
_logger = logging.getLogger(__name__)
from odoo.http import request

LIVE_URLS = [

            ]
class FundsRequest(models.Model):
    _name = "funds.request"
    _description = "Fund Requests"
    _inherit = ['mail.thread','mail.activity.mixin', 'image.mixin']

    name = fields.Char(default="New",copy=False)
    wallet_id = fields.Many2one('user.wallet',required=True)
    user_id = fields.Many2one('res.users',related='wallet_id.user_id',store=True)
    amount = fields.Monetary()
    company_id = fields.Many2one('res.company', string='Company', required=True,
        default=lambda self: self.env.company)    
    currency_id = fields.Many2one(related="company_id.currency_id",store=True)
    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('pre_approved', 'Pre-Approved'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string="Status",tracking=True,required=True,default="draft")
    creater = fields.Boolean(compute="_compute_not_creator")
    receiver = fields.Boolean(compute="_compute_not_creator")
    reason_for_reject_id = fields.Many2one('cancel.reason')
    to_preapprove = fields.Boolean()
    preapprover_id = fields.Many2one('res.users')
    approver_id = fields.Many2one('res.users')
    preapprover = fields.Boolean(compute="_compute_pre_approver")
    notes = fields.Text()
    receiver_id = fields.Many2one('res.users')

    def _compute_pre_approver(self):
        for rec in self:
            if self.env.user.id == rec.preapprover_id.id:
                rec.preapprover = True
            else:
                rec.preapprover = False


    @api.model_create_multi
    def create(self, vals_list):
        for val in vals_list:
            if val.get('name', 'New') == 'New':
                seq = self.env['ir.sequence'].sudo().search(
                    [('code', '=', 'funds.request')])
                val['name'] = f'{seq.prefix}{str(seq.number_next_actual).zfill(seq.padding)}'
                seq.number_next_actual += seq.number_increment
        res = super(FundsRequest, self).create(vals_list)
        return res


    def _compute_not_creator(self):
        for rec in self:
            if self.env.user.id == rec.create_uid.id:
                rec.creater = True
            else:
                rec.creater = False
            if self.env.user.id == rec.receiver_id.id:
                rec.receiver = True
            else:
                rec.receiver = False

    def action_confirm(self):
        for rec in self:
            rec.sudo().write({
                'state':'confirmed',
            })
            rec.sudo().send_mail_to_approvers()
            
    def action_pre_approve(self):
        code_record = self.env['authorization.code'].sudo().create({
                        'funds_request_id': self.id,
                    })
        email_template = self.env.ref('eagle_mpesa_client.mail_template_wallet_authorization_code')
        context = {}
        context.update({
                'code':code_record.code,
            })
        current_host_url = request.httprequest.host_url


        email_to = self.env.user.email
        email_values = {
            'email_to': email_to,
            'email_cc': False,
            'auto_delete': True,
            'recipient_ids': [],
            'partner_ids': [],
            'scheduled_date': False,
        }
        with self.env.cr.savepoint():
            email_template.with_context(**context).send_mail(
                self.env.user.id, force_send=True, raise_exception=True, email_values=email_values, email_layout_xmlid='mail.mail_notification_light'
            )
        if self.state == 'confirmed':
            message = f"An authorization code has been sent to {self.env.user.email}\nKindly enter the code and pre-approve this funds allocation"
        else:
            message = f"An authorization code has been sent to {self.env.user.email}\nKindly enter the code and approve this funds allocation"

        message_id = self.env['wizard.wallet'].create({
            'message':message,
            'funds_request_id':self.id,
            'sent_code':True,
        })
       
        action = self.env["ir.actions.actions"]._for_xml_id("eagle_mpesa_client.wizard_transaction_action")
        action['target'] = 'new'
        action['res_id'] = message_id.id
        return action
     

   
    def action_reject(self):
        if self.state not in ['confirmed','pre_approved']:
            raise ValidationError("You cannot an allocation not in confirmed state")
        reject_id = self.env['reject.funds.request'].create({
            'funds_request_id':self.id,
        })
        return {
                'name': _("Reject Funds Request"),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'reject.funds.request',
                'res_id': reject_id.id,
                'target':'new',
            }

    def action_approve(self):
        company_wallet = self.env['user.wallet'].sudo().search([('company_wallet','=',True),('company_id','=',self.wallet_id.company_id.id)])
        company_wallet.sudo().activate_on_eagle()
        if company_wallet.wallet_balance < self.amount:
            raise ValidationError("Not enough balance on company wallet.")
        current_host_url = request.httprequest.host_url
       
        email_to = self.env.user.email
        message_id = self.env['wizard.wallet'].create({
            'sender_wallet':company_wallet.id,
            'receiver_wallet':self.wallet_id.id,
            'funds_request_id':self.id,
            'user_email': email_to,
            'amount':self.amount,
        })
        return message_id.sudo().action_send()

    def send_mail_to_approvers(self):
        if self.state == 'approved':
            email_template = self.env.ref('eagle_mpesa_client.mail_template_approvals_wallet_allocation_approved')
            users = self.env.ref('eagle_mpesa_client.group_kpayment_approver_wallet').users


        elif self.state == 'pre_approved':
            email_template = self.env.ref('eagle_mpesa_client.mail_template_approvals_wallet_allocation_pre_approved')
            users = self.env.ref('eagle_mpesa_client.group_kpayment_approver_wallet_two').users

        else:
            email_template = self.env.ref('eagle_mpesa_client.mail_template_approvals_wallet_allocation')
            users = self.env.ref('eagle_mpesa_client.group_kpayment_approver_wallet_one').users

        context = {}
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        link = base_url + '/web#id=%d&view_type=form&model=%s' % (self.id, self._name)
        

        context.update({
                'name':'Funds Request',
                'record_name':self.name,
                'creater':self.create_uid.name,
                'pre_approver':self.preapprover_id.name if self.preapprover_id else False,
                'approver':self.approver_id.name if self.approver_id else False,
                'amount':"{:,.1f}".format(self.amount)+f" {self.currency_id.name}",
                'receiver':self.user_id.name,
                'link':link,
                'reason_set':True if self.notes else False,
                'reason':self.notes,
            })
        
        for user in users:
                # if user.id !=  self.env.user.id and user.id != self.user_id.id and self.env.company.id in user.company_ids.ids:
                current_host_url = request.httprequest.host_url


              
                email_to = user.email
                email_values = {
                    'email_to': user.email,
                    'email_cc': False,
                    'auto_delete': True,
                    'recipient_ids': [],
                    'partner_ids': [],
                    'scheduled_date': False,
                }
                with self.env.cr.savepoint():
                    email_template.with_context(**context).send_mail(
                        user.id, force_send=True, raise_exception=True, email_values=email_values, email_layout_xmlid='mail.mail_notification_light'
                    )