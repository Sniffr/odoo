from pytz import timezone, UTC
from odoo import Command
import math
from odoo.tools.misc import groupby as tools_groupby
from odoo import api, fields, models, _, SUPERUSER_ID
import json
from collections import defaultdict
from dateutil.relativedelta import relativedelta
import traceback
from odoo.tools import float_compare, float_round, is_html_empty, float_is_zero
from collections import Counter
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _
from datetime import datetime, timedelta
import logging
_logger = logging.getLogger(__name__)

class PayBatchLineInherit(models.Model):
    _inherit = "pay.batch.line"
    
    eagle_payment_id = fields.Many2one('eagle.payment')
    