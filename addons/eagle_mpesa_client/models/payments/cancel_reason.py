from itertools import groupby

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime

class CancelReason(models.Model):
    _name = "cancel.reason"
    _description = "Cancel Reason"
    _inherit = ['mail.thread','mail.activity.mixin', 'image.mixin']

    name = fields.Char(default="New",copy=False)
