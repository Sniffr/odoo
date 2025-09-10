

# -*- coding: utf-8 -*-
from odoo.http import request
from odoo import http
import logging
_logger = logging.getLogger(__name__)


class PosMpesaApi(http.Controller):

    def sendToPosPaymentBusChannel(self, data):
        _logger.info(
            f"************SENDING KPAY RESPONSE DATA TO BUS CHANNEL************{data}")
        # Send the live data to the frontend using the bus service
        channel = "mpesa_payment_channel"
        message = {
            "data": data,
            "channel": channel
        }
        http.request.env["bus.bus"]._sendone(channel, channel, message)

    @http.route('/kpay-callback', auth='public', methods=['POST'], csrf=False)
    def live_callback(self, **kw):

        # sample_response
        # {
        #     'transaction_id': 'a8eeafc6-8d24-46ff-b754-cf298990b374',
        #     'status': 'TS',
        #     'amount': 5.0,
        #     'currency': 'KES',
        #     'message': 'Transaction was successfull',
        #     'phone': '254746352911',
        #     'type': 'ussd'
        # }

        _logger.info(
            "(************CALLBACK RETURNED INFO*****************{}********)".format(request.get_json_data()))
        response = request.get_json_data()
        status = response['status']
        payment_model = ""

        # if response['provider_code'] == 'airtel':
        #     payment_model = 'airtel.temp.payment'
        # elif response['provider_code'] == 'mtn':
        #     payment_model = 'mtn.temp.payment'
        # elif response['provider_code'] == 'mpesa':
        payment_model = 'temp.order'

        if status == 'TS':
            http.request.env[payment_model].sudo(
            ).create_temp_order(response)
            self.sendToPosPaymentBusChannel(response)
