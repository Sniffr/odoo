# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import pprint

from werkzeug import urls

from odoo import _, models,fields
from odoo.exceptions import UserError, ValidationError

from odoo.addons.payment import utils as payment_utils
from odoo.addons.eagle_web_payments import const
from odoo.addons.eagle_web_payments.controllers.main import KPayController


_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'


    
    eagle_transaction_id = fields.Char(
        string='Hippo Transaction ID',
    )
    eagle_mobile = fields.Char(
        string='Mobile Number',
    )
    
    subscription_code = fields.Char(
        string='Subscription Code',
    )

    mpesa_type = fields.Char(
        string='MPESA Type',
    )


    
    
    def _get_last_txn(self,uid):
        """ Return the last transaction of the recordset.

        :return: The last transaction of the recordset, sorted by id.
        :rtype: recordset of `payment.transaction`
        """






        return self.env['payment.transaction'].sudo().search([("user_id","=",uid)],order="id asc",limit=1)

    

    def _set_draft(self):
        self.write({
                'state': "draft",
            })
        
    def get_duuka_txn(self,txn_id):

        duuka_airtel_transaction = self.env['airtel.temp.payment'].search([("transaction_id","=",txn_id)])
        if duuka_airtel_transaction:
            return duuka_airtel_transaction
        duuka_mtn_transaction = self.env['mtn.temp.payment'].search([("transaction_id","=",txn_id)])
        if duuka_mtn_transaction:
            return duuka_mtn_transaction
        duuka_mpesa_transaction = self.env['mpesa.temp.payment'].search([("transaction_id","=",txn_id)])
        if duuka_mpesa_transaction:
            return duuka_mpesa_transaction
        

    def complete_duuka_txn(self,notification_data,transaction):
        if notification_data['status'] == "TS":
            _user = self.env['res.users'].sudo().browse(notification_data['uid'])
            if not _user.sudo().company_id.kola_id:
                _user.company_id.sudo().write({
                    "kola_id": notification_data['kola_id']
                })

            #Create an internal User if the user is not.registerSubscription
            UserSudo = self.env['res.users'].sudo().browse(notification_data['uid'])
            if notification_data['product_code'] == "KSAAS":
                UserSudo.set_internal_user()
                _logger.info(f"subscription Data got {notification_data}")
                if "saas_subscription" in notification_data:
                    UserSudo.registerSubscription(notification_data['saas_subscription'])

                            



        

    def _process_notification_data(self, notification_data):
        # """ Override of payment to process the transaction based on kPay data.

        # Note: self.ensure_one()

        # :param dict notification_data: The notification data sent by the provider.
        # :return: None
        # :raise ValidationError: If inconsistent data were received.
        # """
        try:

            Transaction = self.env['payment.transaction'].sudo()
            #TODO: Should not Manually set the current Transaction
            if "reference" in notification_data:
                current_txn =  Transaction.search([("reference","=",notification_data['reference'])])
            else:
                current_txn =  Transaction.search([("eagle_transaction_id","=",notification_data['transaction_id'])])

         
            self = current_txn


            _logger.info(f"CURENT TXN{current_txn}{notification_data}")
            super()._process_notification_data(notification_data)


            if self.provider_code != 'eagle':
                return
            if "reference" in notification_data:

                print(notification_data,self.payment_method_id.code)

                phone = ""
                if self.payment_method_id.code == "eagle_airtel":
                    phone = notification_data['airtel_phone'] 
                elif self.payment_method_id.code == "eagle_mtn" :
                    phone= notification_data['mtn_phone']
                else:
                    phone= notification_data['mpesa_phone']
                payload = {
                    "phone":phone ,        # Check if the phone number matches the specified format
                    "txn": current_txn 
                }
                order = self.env['sale.order'].sudo().search([("name","=",self.reference.split("-")[0])])
              
                order.sudo().write({
                    "payment_txn_id":current_txn.id
                })
                response = self.provider_id._eagle_make_request(
                    '/make/payment', payload=payload, method='GET'
                )
                self.provider_reference = response['transaction_id']
            else:
                pass


            if notification_data['status'] == "TS":
                transaction = False
        
                transaction = Transaction.search([("eagle_transaction_id","=",current_txn.eagle_transaction_id)]) 

          
                if transaction:
                    self._set_done()

                    #TODO Handle  these next processes to another THREAG!tt
                    #update kola ID
                    _user = self.env['res.users'].sudo().browse(notification_data['uid'])
                

            elif notification_data['status'] == "TF":
                self._set_error(
                    _("An error occurred during the processing of your payment. Please try again.")
                )
            else:
                #TODO Doesn't look Right
                self._set_draft()

            return 
  

        except Exception as e:
            _logger.info("\n\n{}\n\n".format(e))
            return False
