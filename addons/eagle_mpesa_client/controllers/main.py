# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request, route
from odoo.tools import lazy
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo import http, SUPERUSER_ID, tools, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools.json import scriptsafe as json_scriptsafe
import base64
import xmlrpc.client
from datetime import datetime, timedelta
import json
import base64
import requests
from odoo import fields, models, api, _
from odoo.tools.json import scriptsafe as json_scriptsafe
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.fernet import Fernet
from psycopg2 import OperationalError
import logging
_logger = logging.getLogger(__name__)





class KPayments(http.Controller):

    @http.route('/eagle/payroll/callback', auth='public',type='http',  methods=['post','put'], csrf=False)
    def kpayments_callback(self,**kwargs):
        for i in range(0,5):
            _logger.info("disbursements callback")
        response = request.get_json_data()
        if response.get('pay_line_ids'):
            for line_response in response.get('pay_line_ids'):
                if line_response.get('eagle_client_id'):
                    _logger.info("point b")
                    _logger.info("point b")
                    _logger.info("point b")
                    disbursement = request.env['eagle.payment'].with_user(SUPERUSER_ID).sudo().search([('id','=',int(line_response.get('eagle_client_id')))])
                    if disbursement:
                        with request.env.cr.savepoint():
                            _logger.info("point c")
                            _logger.info(line_response)
                            _logger.info("point c")
                    
                            disbursement.with_user(SUPERUSER_ID).write({
                                'fail_reason':line_response.get('reason') if line_response.get('reason') else False,
                                'state':line_response.get('state'),
                            })
                            if disbursement.state == 'done':
                                disbursement.with_user(SUPERUSER_ID).execute_rest()
                            elif disbursement.state in ['cancel','failed'] and disbursement.payslip_id:
                                disbursement.with_user(SUPERUSER_ID).cancel_rest()



    @http.route('/eagle/expense/callback', auth='public',type='http',  methods=['post','put'], csrf=False)
    def expenses_callback(self,**kwargs):
        
        for i in range(0,5):
            _logger.info("eagle callback")
        
        response = request.get_json_data()
        data = {
            'created':False,
        }
        _logger.info(response)

        if response.get('transaction_id') and response.get('status') == 'done':
            _logger.info("get payment")
            _logger.info("get payment")

            payment = request.env['eagle.payment'].with_user(SUPERUSER_ID).sudo().search([
                ('reference','=',response.get('transaction_id')),
                ('company_id','=',response.get('company_id')),
                ('create_uid','=',int(response.get('user_id'))),
            ])
            if payment:
                _logger.info("payment exists")
                _logger.info("payment exists")
                pass
            else:
                with request.env.cr.savepoint():
                    _logger.info("payment getting created")
                    _logger.info("payment getting created")
                    payment = request.env['eagle.payment'].with_user(int(response.get('user_id'))).sudo().create({
                        'reference':response.get('transaction_id'),
                        'company_id':int(response.get('company_id')),
                        'amount':response.get('amount'),
                        'charges':response.get('charges'),
                        'notes':response.get('description'),
                        'pettycash_payment':True,
                        'state':'done',
                        'disburse_to':response.get('disburse_to'),
                        'phone':response.get('phone'),
                    })
                    payment.with_user(int(response.get('user_id'))).with_company(int(response.get('company_id'))).sudo().create_expense_callback()
                    data = {
                        'created':True,
                    }
        response= http.Response(
            response=json.dumps(data),
            status=202,
            content_type='application/json;charset=utf-8'
        )
        return response 
            
    @http.route('/eagle/wallet/callback', auth='public',type='http',  methods=['post','put'], csrf=False)
    def eagle_wallet_callback(self,**kwargs):
        for i in range(0,5):
            _logger.info("eagle update callback")
        
        response = request.get_json_data()
        data = {
            'created':False,
        }
        _logger.info(response)

        if response.get('wallet_name'):
            wallet = request.env['user.wallet'].with_user(SUPERUSER_ID).sudo().search([
                ('name','=',response.get('wallet_name')),
            ])
            acount_request = request.env['account.request'].with_user(SUPERUSER_ID).sudo().search([
                    ('requested_account_no','=',response.get('requested_account_no')),
                ])
            if not wallet:
                # acount_request = request.env['account.request'].with_user(SUPERUSER_ID).sudo().search([
                #     ('requested_account_no','=',response.get('requested_account_no')),
                # ])
                acount_request.with_user(SUPERUSER_ID).write({
                    'state':response.get('state'),
                    'reason_for_reject':response.get('reason_for_reject'),
                })
                acount_request.with_user(SUPERUSER_ID).company_id.sudo().write({
                    'eagle_user_name':response.get('eagle_user_name'),
                    'eagle_api_key':response.get('eagle_api_key'),
                    'hippo_client_id':response.get('hippo_client_id'),
                    'hippo_api_key':response.get('hippo_api_key'),
                    'hippo_public_key':response.get('hippo_public_key'),

                })

                if acount_request.state == 'approved':
                    wallet = request.env['user.wallet'].with_user(SUPERUSER_ID).create({
                        'name': response.get('wallet_name'),
                        'partner_id': acount_request.with_user(SUPERUSER_ID).company_id.partner_id.id,
                        'company_id':acount_request.company_id.id,
                    })
                   

            wallet.with_user(SUPERUSER_ID).update_payment_provider_keys(response)

                    
            if wallet:
                wallet.with_user(SUPERUSER_ID).with_company(wallet.company_id.id).send_to_other_channels(response)
                wallet.with_user(SUPERUSER_ID).with_company(wallet.company_id.id).activate_on_eagle()
            try:
                acount_request.with_user(SUPERUSER_ID).send_notify_email()
            except Exception as e:
                _logger.info("")
                _logger.info("")
                _logger.info(e)
                _logger.info("")
                _logger.info("")
                
        elif response.get('requested_account_no'):
            if response.get('state') == 'rejected':
                acount_request = request.env['account.request'].with_user(SUPERUSER_ID).sudo().search([
                        ('requested_account_no','=',response.get('requested_account_no')),
                    ])
                acount_request.with_user(SUPERUSER_ID).write({
                    'state':response.get('state'),
                    'reason_for_reject':response.get('reason_for_reject'),
                })
                try:
                    acount_request.with_user(SUPERUSER_ID).send_notify_email()
                except Exception as e:
                    _logger.info("")
                    _logger.info("")
                    _logger.info(e)
                    _logger.info("")
                    _logger.info("")

        elif response.get('transaction_id'):
            request.env['account.request'].with_user(SUPERUSER_ID).process_response(response)
            request.env['user.wallet'].with_user(SUPERUSER_ID).send_to_other_channels(response)
            if response.get('client_wallet_name'):
                wallet = request.env['user.wallet'].with_user(SUPERUSER_ID).sudo().search([
                    ('name','=',response.get('client_wallet_name')),
                ])
                if wallet:
                    wallet.with_user(SUPERUSER_ID).with_company(wallet.company_id.id).activate_on_eagle()