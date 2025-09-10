# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import pprint

import requests
from werkzeug.urls import url_join
from odoo.http import request
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

import base64
import json
import re
import uuid
import os
import json


_logger = logging.getLogger(__name__)


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('mpesa', "MPESA"),('vodacom','Vodacom')], ondelete={
            'mpesa': 'set default',
            'vodacom': 'set default',
            }
    )
    