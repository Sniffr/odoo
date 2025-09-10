from odoo import fields, models, api, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta, date
import logging
from odoo.http import request, route
import requests
import json
import re
import base64
_logger = logging.getLogger(__name__)


class AccountRequest(models.Model):
    _name = "account.request"
    _description = "Account Request"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'image.mixin']
    _order = "id desc"

    name = fields.Char(
        string="Reference",
        index='trigram',
        default=lambda self: _('New'),
        copy=False,
        readonly=True,
        tracking=True
    )
    requested_account_no = fields.Char(string="Account Number", required=True, tracking=True)
    state = fields.Selection([
        ('new', 'New'),
        ('sent', 'Sent'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string="Status", tracking=True, required=True, default="new", copy=False)

    ### Optional - Auto Track User and Date Info
    requested_by = fields.Many2one('res.users', string="Requested By", default=lambda self: self.env.user, readonly=True)
    company_id = fields.Many2one('res.company', string='Company', required=True,
        default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency',related="company_id.currency_id",store=True)
    enable_kola_mpesa = fields.Boolean(related="company_id.enable_kola_mpesa",store=True)
    consent_to_collect_funds = fields.Boolean(
        string="Consent to Collect Funds",
        help="Allow Kola to collect money on your behalf.",
        default=False,
        required=True,
        tracking=True,
    )
    paybill_number = fields.Char(default="4455890",readonly=True)
    reason_for_reject = fields.Char()
    
    @api.constrains('requested_account_no')
    def _validate_requested_account_no(self):
        pattern = r'^[A-Za-z0-9]{4,6}$'  # Alphanumeric, 4 to 6 characters, no spaces
        for record in self:
            if record.requested_account_no and not re.match(pattern, record.requested_account_no):
                raise ValidationError("Account number must be 4 to 6 characters long, and contain only letters and numbers without spaces.")

    @api.onchange('requested_account_no')
    def _onchange_account_no(self):
        pattern = r'^[A-Za-z0-9]{4,6}$'  # Alphanumeric, 4 to 6 characters, no spaces
        for record in self:
            if record.requested_account_no and not re.match(pattern, record.requested_account_no):
                raise ValidationError("Account number must be 4 to 6 characters long, and contain only letters and numbers without spaces.")


    @api.constrains('company_id')
    def _api_check_requested_account_no(self):
        for rec in self:
            # if not rec.company_id.enable_kola_mpesa:
            #     raise ValidationError("Kola Mpesa is not enabled for your company.")
            existing_request = self.env['account.request'].sudo().search([
                ('id','!=',rec.id),
                ('state','!=','rejected'),
                ('company_id','=',rec.company_id.id),
            ])
            _logger.info(f"The existing Request *******{existing_request}")
            if existing_request:
                raise ValidationError(f"You already have an existing request, {existing_request.name}.")
            if rec.company_id.country_id.code != 'KE':
                raise ValidationError(f"Account Requests not yet activated for {rec.company_id.country_id.name}.\nOnly Kenyan companies can make requests.")

    # Sequence logic
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals['name'] == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('account.request') or _('New')
        return super().create(vals_list)

    # Actions to change state (buttons in form view can call these)
    def action_confirm(self):
        for rec in self:
            if rec.state != 'new':
                raise UserError(_("Only confirmed requests can be approved."))
            rec.state = 'confirmed'

   

    def action_reject(self):
        for rec in self:
            if rec.state in ('approved',):
                raise UserError(_("Approved requests cannot be rejected."))
            rec.state = 'rejected'

    

    def action_send(self):
        if not self.consent_to_collect_funds:
            raise ValidationError("Consent is required for Kola to receive payments on your behalf.")
        if not self.company_id.enable_kola_mpesa:
            self.company_id.sudo().enable_kola_mpesa = True

        try:
            self.check_or_create_provider()
        except Exception as e:
            _logger.info("")
            _logger.info("")
            _logger.info(e)
            _logger.info("")
            _logger.info("")

        # if current_host_url in LIVE_URLS:
        home_url = request.httprequest.host_url

        encoded_url = "aHR0cHM6Ly9lYWdsZS5rb2xhcHJvLmNvbS9jcmVhdGUvYWNjb3VudC9yZXF1ZXN0"
        url = base64.b64decode(encoded_url).decode()
        

        payload = json.dumps({
            'requested_account_no': self.requested_account_no,
            'company_name': self.company_id.name,
            'request_from': self.company_id.get_base_url(),
            'currency_id': self.currency_id.name,
            'country_id': self.company_id.country_id.code,
            'expense_database_callback': f"{self.company_id.get_base_url()}/eagle/expense/callback",
            'expense_company_id': self.company_id.id,
            'collections_call_back_url': f"{self.company_id.get_base_url()}/eagle/wallet/callback",
            'partner_id': self.company_id.name,
            'service': f"{self.company_id.partner_id.name} Kola Mpesa",
        })
        _logger.info(f"This is the payload ******* {payload}")
        headers = {
            'Target-Environment': 'test',
            'Content-Type': 'application/json',
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        response_dict = response.json()
        _logger.info("")
        _logger.info("")
        _logger.info(response_dict)
        _logger.info("")
        _logger.info("")
        if response_dict.get("success"):
            self.sudo().write({'state':'sent'})
        elif response_dict.get("message"):
            raise ValidationError(f"{response_dict.get('message')}")
        else:
            raise ValidationError("An unexpected error occured.")
        
        # return response_dict



        
    def send_notify_email(self):
        if self.state == 'approved':
            email_template = self.env.ref('eagle_mpesa_client.mail_template_account_request_approved')
        else:
            email_template = self.env.ref('eagle_mpesa_client.mail_template_account_request_rejected')

        context = {}
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        link = base_url + '/web#id=%d&view_type=form&model=%s' % (self.id, self._name)
        

        context.update({
                'requested_account_no':self.requested_account_no,
                'reason_for_reject':self.reason_for_reject,
            })
        users = [self.create_uid]
        for user in users:
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

    def check_or_create_provider(self):
        pass

    def process_response(self,vals):
        _logger.info("Initiated stk")
        _logger.info("Initiated stk")
        _logger.info(vals)
        _logger.info("Initiated stk")
        _logger.info("Initiated stk")
      