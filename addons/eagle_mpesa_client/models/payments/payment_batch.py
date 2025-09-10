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
LIVE_URLS = [

            ]
class PaymentBatch(models.Model):
    _name = "payment.batch"
    _description = "Payment Batch"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'image.mixin']
    _order = "id desc"

    _sql_constraints = [
        ('name', 'unique(name)', 'Name already exists!'),
    ]

    name = fields.Char(default="New",copy=False)
    amount = fields.Monetary(string="Amount",compute="_compute_total",store=True)
    total = fields.Monetary(compute="_compute_total",store=True)
    charges = fields.Monetary(compute="_compute_total",store=True)
    state = fields.Selection(selection=[
        ('draft','Draft'),
        ('pending','Pending'),
        ('pre_approved', 'Pre-approved'),
        ('approved', 'Approved'),
        ('cancelled','Cancelled'),
    ], string="State", default='draft', tracking=True)
    eagle_payment_ids = fields.One2many('eagle.payment','payment_batch_id')
    company_id = fields.Many2one('res.company',required=True,default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency',related="company_id.currency_id",store=True)
    done_txns = fields.Integer(compute="_compute_done_txns")
    failed_txns = fields.Integer(compute="_compute_failed_txns")
    level_progress = fields.Integer(string="Success Rate", help="Progress of successful lines.",compute="_compute_level_progress")
    cancel_reason_id = fields.Many2one('cancel.reason')
    test_recipient_email = fields.Char(required=True,help="This email will receive authentication codes for testing purposes.")
    

    @api.depends('eagle_payment_ids.amount','eagle_payment_ids.charges','eagle_payment_ids.total')
    def _compute_total(self):
        for rec in self:
            rec.amount = sum(rec.eagle_payment_ids.mapped('amount'))
            rec.charges = sum(rec.eagle_payment_ids.mapped('charges'))
            rec.total = sum(rec.eagle_payment_ids.mapped('total'))

    @api.depends('eagle_payment_ids.state')
    def _compute_level_progress(self):
        for rec in self:
            if rec.eagle_payment_ids:
                finished = [line for line in rec.eagle_payment_ids if line.state == 'done']
                rec.level_progress = (len(finished)/len(rec.eagle_payment_ids))*100
            else:
                rec.level_progress = 0

    def _compute_done_txns(self):
        for rec in self:
            rec.done_txns = len([each.id for each in rec.eagle_payment_ids if each.state == 'done'])

    def _compute_failed_txns(self):
        for rec in self:
            rec.failed_txns = len([each.id for each in rec.eagle_payment_ids if each.state == 'cancel'])

    def view_successful(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("eagle_mpesa_client.eagle_payment_action")
        ids = [each.id for each in self.eagle_payment_ids if each.state == 'done']
        domain = [('id', 'in', ids)]
        context={}
        views = [(self.env.ref('eagle_mpesa_client.eagle_payment_list').id, 'list'), (False, 'form')]
        return dict(action, domain=domain, context=context, views=views)

    def view_failed(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("eagle_mpesa_client.eagle_payment_action")
        ids = [each.id for each in self.eagle_payment_ids if each.state in ['cancel','failed']]
        domain = [('id', 'in', ids)]
        context={}
        views = [(self.env.ref('eagle_mpesa_client.eagle_payment_list').id, 'list'), (False, 'form')]
        return dict(action, domain=domain, context=context, views=views)

    @api.model_create_multi
    def create(self, vals_list):
        for val in vals_list:
            if val.get('name', 'New') == 'New':
                seq = self.env['ir.sequence'].sudo().search(
                    [('code', '=', 'payment.batch')])
                val['name'] = f'{seq.prefix}{str(seq.number_next_actual).zfill(seq.padding)}'
                seq.number_next_actual += seq.number_increment
        res = super(PaymentBatch, self).create(vals_list)
        return res

    def confirm_payment_batch(self):
        return self.send_mail()

    def preapprove_payment_batch(self):
        return self.send_mail()

    def approve_payment_batch(self):
        return self.send_mail()

    def reject_payment_batch(self):
        reject_id = self.env['reject.payment'].create({
            'payment_batch_id':self.id,
        })
        return {
                'name': _("Reject/Cancel Payment Batch"),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'reject.payment',
                'res_id': reject_id.id,
                'target':'new',
            }

    def send_mail(self):
        code_record = self.env['authorization.code'].sudo().create({
                        'payment_batch_id': self.id,
                    })
        email_template = self.env.ref('eagle_mpesa_client.mail_template_payment_authorization_code')
        context = {}
        context.update({
                'code':code_record.code,
            })
        current_host_url = request.httprequest.host_url
        
        email_values = {
            'email_to': self.test_recipient_email,
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
        if self.state == 'draft':
            message = f"An authorization code has been sent to {self.env.user.email}\nKindly enter the code and confirm this payment batch"
        elif self.state == 'pending':
            message = f"An authorization code has been sent to {self.env.user.email}\nKindly enter the code and pre-approve this payment batch"
        elif self.state == 'pre_approved':
            message = f"An authorization code has been sent to {self.env.user.email}\nKindly enter the code and approve this payment batch"

        message_id = self.env['wizard.payment'].create({
            'message':message,
            'payment_batch_id':self.id,
            'sent_code':True,
        })
       
        action = self.env["ir.actions.actions"]._for_xml_id("eagle_mpesa_client.wizard_payment_action")
        action['target'] = 'new'
        action['res_id'] = message_id.id
        return action