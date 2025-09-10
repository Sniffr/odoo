from odoo import fields, models, api, _, registry, Command, SUPERUSER_ID
import time
import requests
import json
import pprint
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError, UserError
import threading
import os
import ast
import re
from ...models.eagle.eagle import EagleConnection
from odoo.http import request

import logging
_logger = logging.getLogger(__name__)
Regex = re.compile(r'^(?:\+254|0|254)(70[0-9]{7}|71[0-9]{7}|72[0-9]{7}|74[0-3][0-9]{6}|74[5-6][0-9]{6}|748[0-9]{6}|75[7-9][0-9]{6}|76[8-9][0-9]{6}|79[0-9]{7}|11[2-5][0-9]{6})$|^(?:\+256|0|256)(70[0-9]{7}|75[0-9]{7}|74[0-9]{7}|20[0-9]{6}|77[0-9]{7}|78[0-9]{7}|76[0-9]{7}|39[0-9]{6}|31[0-9]{6})$')
LIVE_URLS = [

            ]

class EaglePayment(models.Model):
    _name = "eagle.payment"
    _description = "Eagle Payment"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'image.mixin']
    _order = "id desc"

    _sql_constraints = [
        ('name', 'unique(name)', 'Name already exists!'),
    ]

    name = fields.Char(string="Payment ID",default="New",copy=False)
    amount = fields.Monetary(string="Amount")
    total = fields.Monetary(compute="_compute_total",store=True)
    charges = fields.Monetary()

    state = fields.Selection(selection=[
        ('draft','Draft'),
        ('submitted','Submitted'),
        ('approved','Approved'),
        ('pending','Pending'),
        ('done', 'Completed'),
        ('cancel', 'Cancelled'),
        ('failed','Failed'),
    ], string="State", default='draft', tracking=True)
    
    employee_id = fields.Many2one('hr.employee',string="Recipient")
    identification_id = fields.Char(required=True)
    work_phone = fields.Char(related="employee_id.work_phone",store=True,readonly=False,string="Phone")
    phone_validity = fields.Selection(selection=[
        ('invalid','Invalid'),
        ('valid', 'Valid'),
    ], default='invalid', tracking=True)

    fail_reason = fields.Char(string="Reason")
    payslip_id = fields.Many2one('hr.payslip')
    payslip_run_id = fields.Many2one('hr.payslip.run')
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company',required=True,default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency',related="company_id.currency_id",store=True)
    id_type = fields.Selection(
        selection =[
            ('01', 'National ID'),
            ('02', 'Military ID'),
            ('05', 'Passport'),
            ],
        default="01",string="ID Type",required=True,
    )
    field_payment = fields.Boolean()
    pettycash_payment = fields.Boolean()
    casual_payment = fields.Boolean()
    payment_type = fields.Selection(
        selection =[
            ('casual_payment', 'Casual Payment'),
            ('field_payment', 'Field Payment'),
            ('pettycash_payment', 'Petty Cash Payment'),
            ],
        compute="_compute_payment_type",
        store=True,
    )
    wallet_id = fields.Many2one('user.wallet')
    payment_batch_id = fields.Many2one('payment.batch')
    phone = fields.Char(
        string='Phone',
        required=True,
    )
    partner_id = fields.Many2one('res.partner',related="create_uid.partner_id",store=True,string="Partner")
    disburse_to = fields.Selection(selection=[
        ('phone', 'Phone Number'),
        ('till', 'Till Number'),
        ('pay_bill_number', 'Pay Bill Number'),
    ], string="Disburse To", default='phone',required=True)
    expense_category_id = fields.Many2one('product.product',domain="[('can_be_expensed','=',True)]")
    notes = fields.Text()
    expense_id = fields.Many2one('hr.expense')
    test_recipient_email = fields.Char()
    reference = fields.Char()

    def validation_checks(self):
        company_wallet = self.env['user.wallet'].sudo().search([('partner_id','=',self.company_id.partner_id.id)])
        if company_wallet.wallet_balance == 0:
            raise ValidationError("You have no funds on your shop wallet account.")
        if self.amount <= 0:
            raise ValidationError("Amount must be greater than 0.")
        if company_wallet.wallet_balance < self.amount:
            raise ValidationError("Insufficient funds in shop wallet account.")

    def submit_request(self):
        if self.state == 'draft':
            self.validate_numbers()
            self.validation_checks()
            self.sudo().write({'state':'submitted'})

    def approve_request(self):
        if self.state == 'submitted':
            self.validation_checks()
            self.sudo().write({'state':'approved'})

    def send_funds(self):
        if self.state == 'approved':
            # self.validation_checks()
            return self.send_mail()
            # self.sudo().write({'state':'approved'})

    def cancel_request(self):
        self.sudo().write({'state':'cancel'})


        


    @api.depends('field_payment','pettycash_payment')
    def _compute_payment_type(self):
        for rec in self:
            if rec.pettycash_payment:
                rec.payment_type = 'pettycash_payment'
            elif rec.field_payment:
                rec.payment_type = 'field_payment'
            else:
                rec.payment_type = 'casual_payment'

    
    
    @api.model_create_multi
    def create(self, vals_list):
        for val in vals_list:
            if val.get('name', 'New') == 'New':
                seq = self.env['ir.sequence'].sudo().search(
                    [('code', '=', 'eagle.payment')])
                val['name'] = f'{seq.prefix}{str(seq.number_next_actual).zfill(seq.padding)}'
                seq.number_next_actual += seq.number_increment
            if val.get('pettycash_payment') and not val.get('wallet_id'):
                if self.env.user.wallet_id:
                    val['wallet_id'] = self.env.user.wallet_id.id
        res = super(EaglePayment, self).create(vals_list)
        return res

    @api.depends('amount')
    def _compute_total(self):
        for rec in self:
            if rec.payment_type == 'pettycash_payment' and not rec.reference:
                rec.charges = rec.get_charges()
            rec.total = rec.amount + rec.charges

    def get_charges(self):
        pay_line_list = []
        total = 0
        payline_dict = {
            'id':self.id,
            'amount':self.amount,
            'provider_code':'mpesa',
        }
        pay_line_list.append(payline_dict)
        total += self.amount
        vals_dict = {
            'pay_list': pay_line_list,
            'total': total,
        }
        try:
            eagle_connection = EagleConnection(model='eagle.connection',method='get_payment_charges',values=[vals_dict])
            response = eagle_connection.get_response(self.company_id)
        except Exception as e:
            raise ValidationError(e)
        print("")
        print("")
        print("")
        print(response)
        print("")
        print("")
        print("")
        if response.get('error'):
            raise ValidationError(response.get('error'))
        if not response.get("lines"):
            raise ValidationError("An error occured. Please contact technical team.")

        eagle_payment_list = []
        for line_id in response.get('lines'):
            return line_id[1]
        raise ValidationError("An error computing charges.")

    @api.constrains('payment_type')
    def _constrains_pettycash_payment(self):
        for rec in self:
            if rec.payment_type in ['pettycash_payment','field_payment']:
                if not rec.create_uid.wallet_id:
                    raise ValidationError("You have no wallet.")
            

    def check_numbers(self):
        for rec in self:
            if rec.work_phone and rec.state == 'draft':
                pass
                # if not Regex.match(rec.work_phone.replace(" ","")):
                #     raise UserError(f"Invalid number for employee {rec.employee_id.name}.")
                # if rec.phone_validity =='invalid':
                #     raise ValidationError("Phone not validated.")
            
    def validate_numbers(self):
        for rec in self:
            if rec.phone:
                phone = rec.phone
            else:
                phone = rec.work_phone
            if rec.disburse_to == 'phone' and rec.phone:
                if Regex.match(phone.replace(" ","")):
                    rec.sudo().write({
                        'phone_validity':'valid',
                    })
                else:
                    raise ValidationError("Invalid Phone Number.")
            else:
                if phone:
                    rec.sudo().write({
                        'phone_validity':'valid',
                    })

    def create_payment_batch(self):
        eagle_payment_ids = []
        for rec in self:
            if not rec.identification_id:
                raise ValidationError("Kindly enter Valid ID/Passport number.")
            elif rec.state not in ['draft']:
                raise ValidationError(f"{rec.name} Only payments in draft can be moved to a batch.")
            elif rec.phone_validity == 'invalid':
                raise ValidationError(f"{rec.name}'s phone number is not yet validated")
            elif not rec.payment_batch_id:
                eagle_payment_ids.append(rec.id)
            else:
                raise ValidationError(f"{rec.name} already belongs to batch {rec.payment_batch_id.name}")
        if eagle_payment_ids:
            payment_batch = self.env['payment.batch'].sudo().create({
                'eagle_payment_ids':eagle_payment_ids,
            })
            return {
                'name': _(f'Payment Batch {payment_batch.name}'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'payment.batch',
                'res_id': payment_batch.id,
            }
        else:
            raise UserError("No records to create batch")


            
    def make_payment(self):
        # if self.state == 'pending':
            # if not self.id_type(sek)
       
            self.check_numbers()
            main_list = []
            for rec in self:
                if rec.state == 'approved':
                    if not rec.identification_id and rec.payment_type == 'casual_payment':
                        raise ValidationError("Kindly enter Valid ID/Passport number.")
                    if rec.payment_type == 'casual_payment':
                        comment = "SALARY PAYMENTS"
                        phone = rec.phone
                        name = rec.partner_id.name

                    elif rec.payment_type == 'field_payment':
                        rec.wallet_authentication()
                        comment = "Field Payment"
                        phone = rec.phone
                        name = "Field Agent"
                    else:
                        rec.wallet_authentication()
                        comment = "Petty Cash Payment"
                        phone = rec.phone
                        name = rec.partner_id.name

                    sub_vals_dict = {
                        'name':name,
                        'phone':phone,
                        'registered_name':name,
                        'provider_code':'mpesa',
                        'amount':rec.amount,
                        'username':self.env.company.eagle_user_name,
                        'comment':comment,
                        'validate':not rec.field_payment and not rec.pettycash_payment,
                        'company_wallet':True if not rec.field_payment and not rec.pettycash_payment else False,
                        'wallet_id':rec.wallet_id.name if rec.field_payment or rec.pettycash_payment else False,
                        'id':rec.id,
                        'id_number':rec.identification_id,
                        'id_type':rec.id_type,
                    }
                    main_list.append(sub_vals_dict)
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            # callback_url = 'https://webhook.site/c954003b-1cdf-4db0-8081-9052f70feda8'
            # callback_url = 'https://webhook.site/bd6cbad2-a4a2-4df7-9fb6-142af583621b'
            callback_url = f"{base_url}/eagle/payroll/callback"
            print("")
            print("")
            print(callback_url)
            print("")
            print("")
            # raise ValidationError("e")
            try:
                with self.env.cr.savepoint():
                    self.sudo().write({'state':'pending'})
                self.env.cr.commit()
                vals_dict = {'payment_list':main_list,'callback_url':callback_url}
                eagle_connection = EagleConnection(model='eagle.connection',method='make_payment_and_wait',values=[vals_dict])
                response = eagle_connection.get_response(self.company_id)
                _logger.info(response)
                _logger.info(response)
                _logger.info(response)
                _logger.info(response)
                if response == 1:
                    message_id = self.env['message.wizard'].create(
                        {'message': _("Payment(s) Submitted. Kindly wait a few seconds and refresh to confirm the payments.")})
                    return {
                        'name': _('Successfull'),
                        'type': 'ir.actions.act_window',
                        'view_mode': 'form',
                        'res_model': 'message.wizard',
                        # pass the id
                        'res_id': message_id.id,
                        'target': 'new'
                    }

                if response.get("fail"):
                    raise ValidationError(response.get("reason"))
            except Exception as e:
                raise ValidationError(e)

            print(response)
            print(response)
            print(response)
            print(response)


        

    def execute_rest(self):
        if self.payment_type != 'casual_payment':
            try:
                wallet = self.create_uid.wallet_id
                wallet.sudo().activate_on_eagle()
            except Exception as e:
                _logger.info(f"AN ERROR SENDING INFO TO EAGLE: {e}")
        else:
            try:
                wallet = self.env['user.wallet'].search([('partner_id','=',self.company_id.partner_id.id)])
                wallet.sudo().activate_on_eagle()
            except Exception as e:
                _logger.info(f"AN ERROR SENDING INFO TO EAGLE: {e}")

        if self.payslip_id:
            try:
                self.env['account.payment.register'].with_context(active_ids=[self.payslip_id.move_id.id], active_model='account.move').sudo().create({
                        'payment_date': self.payslip_id.date_to,
                        'amount':self.payslip_id.net_wage,
                        'journal_id':self.payslip_id.payslip_run_id.journal_id.id,
                }).sudo()._create_payments()
                _logger.info(self.payslip_id.state)
                _logger.info("payment")
               
            except Exception as e:
                _logger.info("exception")
                _logger.info(e)
                _logger.info("exception")
            if self.payslip_id.state == 'done':
                with self.env.cr.savepoint():
                    self.payslip_id.sudo().action_payslip_paid()
            try:
                self.payslip_id.payslip_run_id.check_mark_as_paid()
            except Exception as e:
                _logger.info("batch exception")
                _logger.info(e)
                _logger.info("batch exception")
        if self.payment_type == 'pettycash_payment':
            try:
                self.create_expense()
            except Exception as e:
                _logger.info(f"AN ERROR OCCURED CREATING EXPENSE: {e}")

        # mpesa_journal = self.env['account.journal'].sudo().search([('mpesa_journal','=',True)])
        # self.env['account.payment.register'].with_context(active_ids=[self.payslip_id.move_id.id], active_model='account.move').with_user(SUPERUSER_ID).create({
        #     'payment_date': self.write_date,
        #     'amount':self.amount,
        #     'journal_id':mpesa_journal.id,
        #     'group_payment':True,
        #     'partner_id':self.employee_id.work_contact_id.id,
        # }).with_user(SUPERUSER_ID)._create_payments()

    def cancel_rest(self):
        try:
            if self.payslip_id and self.state in ['cancel','failed']:
                with self.env.cr.savepoint():
                    self.payslip_id.with_user(SUPERUSER_ID).action_payslip_cancel()
                try:
                    self.payslip_id.payslip_run_id.check_mark_as_paid()
                except Exception as e:
                    _logger.info("batch exception")
                    _logger.info(e)
                    _logger.info("batch exception")
        except Exception as e:
            _logger.info("cancel payslip exception")
            _logger.info(e)
            _logger.info("cancel payslip exception")

    def create_expense(self):
        expense = self.env['hr.expense'].create({
            'name': f"Mpesa {self.notes}",
            'date': self.create_date,
            'payment_mode': 'company_account',
            'total_amount_currency': self.total,
            'employee_id': self.create_uid.employee_id.id,
            'product_id':self.expense_category_id.id,
            'tax_ids':False,
        })

        expense_sheet = self.env['hr.expense.sheet'].create({
            'name':  f"Mpesa {self.notes}",
            'employee_id': self.create_uid.employee_id.id,
            'expense_line_ids':[expense.id],
            'payment_method_line_id':self.company_id.petty_payment_method_line_id.id,
        })
        expense_sheet.action_submit_sheet()
        expense_sheet.action_approve_expense_sheets()
        expense_sheet.action_sheet_move_create()
        self.expense_id = expense.id

    def create_expense_callback(self):
        #creating expense
        
        if not self.create_uid.employee_id:
            self.create_uid.sudo().action_create_employee()
        # if not self.create_uid.employee_id.address_home_id:
        #     self.create_uid.employee_id.address_home_id = self.create_uid.partner_id.id
        _logger.info(self.company_id.eagle_expense_category_id.id)
        _logger.info(self.create_uid.employee_id.company_id)
        _logger.info(self.create_uid.employee_id.company_id.name)
        self.expense_category_id = self.company_id.eagle_expense_category_id.id
        self.partner_id = self.create_uid.partner_id.id
        expense = self.env['hr.expense'].create({
            'name': f"Eagle {self.notes}",
            'date': self.create_date,
            'payment_mode': 'company_account',
            'total_amount': self.total,
            'employee_id': self.create_uid.employee_id.id,
            'product_id':self.company_id.eagle_expense_category_id.id,
            'tax_ids':False,
        })

        expense_sheet = self.env['hr.expense.sheet'].create({
            'name':  f"Eagle {self.notes}",
            'employee_id': self.create_uid.employee_id.id,
            'expense_line_ids':[expense.id],
            'payment_method_line_id':self.company_id.petty_payment_method_line_id.id,
        })
        expense_sheet.action_submit_sheet()
       
        # expense_sheet.approve_expense_sheets()
        expense_sheet.with_user(SUPERUSER_ID)._do_approve()

       
        expense_sheet.with_user(SUPERUSER_ID).action_sheet_move_create()
        
        self.expense_id = expense.id

    def view_expense(self):
        return {
                    'name': _('Expense'),
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'res_model': 'hr.expense',
                    'res_id': self.expense_id.id,
                }


    def make_payment_authenticate(self):
        self.wallet_authentication()
        return self.send_mail()

    def wallet_authentication(self):
        if self.create_uid.id != self.env.user.id:
            raise ValidationError("You cannot make this payment since you do not own it.")
        if not self.create_uid.employee_id:
            raise ValidationError("You must have a related employee.")
        if self.wallet_id.eagle_status != 'active':
            raise ValidationError("Kindly have your wallet activated first.")
        self.wallet_id.sudo().activate_on_eagle()
        if self.wallet_id.wallet_balance < self.total:
            raise ValidationError("Insufficient funds in your wallet.")

    def cancel_payment(self):
        cancel_id = self.env['cancel.payment'].create({
            'eagle_payment_id':self.id,
        })
        return {
                'name': _("Cancel Payment"),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'cancel.payment',
                'res_id': cancel_id.id,
                'target':'new',
            }

    def send_mail(self):
        code_record = self.env['authorization.code'].sudo().create({
                        'eagle_payment_id': self.id,
                    })
        email_template = self.env.ref('eagle_mpesa_client.mail_template_payment_authorization_code')
        context = {}
        context.update({
                'code':code_record.code,
            })

        current_host_url = request.httprequest.host_url
        
        email_values = {
            'email_to': self.env.user.email,
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
            
        message = f"An authorization code has been sent to {self.env.user.email}\nKindly enter the code and approve this payment."
        
        message_id = self.env['single.wizard.payment'].create({
            'message':message,
            'eagle_payment_id':self.id,
            'sent_code':True,
        })
        action = self.env["ir.actions.actions"]._for_xml_id("eagle_mpesa_client.single_wizard_payment_action")
        action['target'] = 'new'
        action['res_id'] = message_id.id
        return action