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
from datetime import datetime, timedelta, date
from ...models.eagle.eagle import EagleConnection
import logging
_logger = logging.getLogger(__name__)


class HrPayslipRun(models.Model):
    _inherit = "hr.payslip.run"

    def pay_with_mpesa(self):
        pay_line_list = []
        total = 0
        for pay_line in self.pay_line_ids:
            if pay_line.to_pay:
                payline_dict = {
                    'id':pay_line.id,
                    'amount':round(pay_line.amount_to_pay,0),
                    'provider_code':'mpesa',
                }
                pay_line_list.append(payline_dict)
                total += round(pay_line.amount_to_pay,0)
        vals_dict = {
            'pay_list': pay_line_list,
            'total': total,
        }
        try:
            eagle_connection = EagleConnection(model='eagle.connection',method='get_payment_charges',values=[vals_dict])
            response = eagle_connection.get_response(self.env.company)
        except Exception as e:
            raise ValidationError(e)
        print("")
        print("")
        print("")
        print(response)
        print("")
        print("")
        print("")
        if response.get('error'):
            raise ValidationError(response.get('error'))
        if not response.get("lines"):
            raise ValidationError("An error occured. Please contact technical team.")

        eagle_payment_list = []
        for pay_line in self.pay_line_ids:
            for line_id in response.get('lines'):
                if pay_line.id == line_id[0]:
                    if not pay_line.eagle_payment_id:
                        eagle_payment = self.env['eagle.payment'].sudo().create({
                            'employee_id':pay_line.employee_id.id,
                            'payslip_id':pay_line.payslip_id.id,
                            'amount':round(pay_line.amount_to_pay,0),
                            'charges':line_id[1],
                            'payslip_run_id':self.id,
                        })
                        pay_line.eagle_payment_id = eagle_payment.id
                        eagle_payment_list.append(eagle_payment.id)
                    else:
                        pay_line.eagle_payment_id.amount = round(pay_line.amount_to_pay,0)
                        pay_line.eagle_payment_id.charges = line_id[1]
                        eagle_payment_list.append(pay_line.eagle_payment_id.id)
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("eagle_mpesa_client.eagle_payment_action")
        domain = [('id', 'in', eagle_payment_list)]
        context = {}
        views = [(self.env.ref('eagle_mpesa_client.eagle_payment_list').id,'list'), (False, 'form')]
        return dict(action, domain=domain, context=context, views=views) 
        
    def button_cancel(self):
        res = super().button_cancel()
        for pay_line in self.pay_line_ids:
            if pay_line.eagle_payment_id:
                if pay_line.eagle_payment_id.state == 'pending':
                    pay_line.eagle_payment_id.sudo().write({'state':'cancel'})
        return res