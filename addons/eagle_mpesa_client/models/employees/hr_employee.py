from odoo import fields, models, api, _
from odoo.tools import groupby
from odoo.exceptions import UserError, ValidationError
import re
import logging
_logger = logging.getLogger(__name__)

Regex = re.compile(r'^(?:\+254|0|254)(70[0-9]{7}|71[0-9]{7}|72[0-9]{7}|74[0-3][0-9]{6}|74[5-6][0-9]{6}|748[0-9]{6}|75[7-9][0-9]{6}|76[8-9][0-9]{6}|79[0-9]{7}|11[2-5][0-9]{6})$|^(?:\+256|0|256)(70[0-9]{7}|75[0-9]{7}|74[0-9]{7}|20[0-9]{6}|77[0-9]{7}|78[0-9]{7}|76[0-9]{7}|39[0-9]{6}|31[0-9]{6})$')

class HrEmployeeInherit(models.Model):
    _inherit = "hr.employee"

    # @api.constrains('work_phone')
    # def _constrain_work_phone(self):
    #     for rec in self:
    #         if rec.work_phone:
    #             if not Regex.match(rec.work_phone.replace(" ","")):
    #                 raise UserError(f"Invalid number for employee {rec.name}.")
