from itertools import groupby

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime

class AccountJournalInherit(models.Model):
    _inherit = "account.journal"

    provider_code = fields.Char(tracking=True)