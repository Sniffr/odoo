# Part of Odoo. See LICENSE file for full copyright and licensing details.

import hmac
import logging
import pprint

from werkzeug.exceptions import Forbidden

from odoo import http
from odoo.exceptions import ValidationError
from odoo.http import request
import json

_logger = logging.getLogger(__name__)


class KPayController(http.Controller):
    _webhook_url = '/payment/eagle/webhook'
    _process_url = '/payment/eagle/process'




    @http.route(_process_url, type='http', auth='public', methods=['POST'], csrf=False)
    def custom_process_transaction(self, **post):
        _logger.info("Handling eagle processing with data:\n%s", pprint.pformat(post))
        post['status'] = "draft"



        request.env['payment.transaction'].sudo()._handle_notification_data('eagle', post)
        return request.redirect('/payment/status')
    



    @http.route(_webhook_url, type='http', methods=['POST','GET'], auth='public',csrf=False)
    def eagle_webhook(self, **data):
        """ Process the notification data sent by eagle to the webhook.

        :return: An empty string to acknowledge the notification.
        :rtype: str
        """
        _logger.info("\n\nHandling redirection from eagle with data:\n%s", pprint.pformat(data))
        _logger.info("\n\n************{}*{}*******dataa\n\n".format(data,request.get_json_data()))
        data = request.get_json_data()

        #TODO: Should check for status,amount
        if data.get('transaction_id'):
            transaction = request.env['payment.transaction'].sudo()._handle_notification_data('eagle', data)

        else:  # The customer cancelled the payment by clicking on the close button.
            pass  # Don't try to process this case because the transaction id was not provided.

        # # Redirect the user to the status page


        #TODO Check if it doesnt reload for other users.


        # user  = request.env['res.users'].browse(request.uid)
        # if data['uid'] == request.uid:
        request.redirect('/payment/status')

  
    


