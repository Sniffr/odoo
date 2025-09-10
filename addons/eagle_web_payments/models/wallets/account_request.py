from odoo import fields, models, api, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.modules.module import get_resource_path
import base64
import logging
_logger = logging.getLogger(__name__)


class AccountRequestInherit(models.Model):
    _inherit = "account.request"
   

    def check_or_create_provider(self):
        try:
            provider = self.env['payment.provider'].sudo().search([('code','=','eagle'),('company_id','=',self.company_id.id)])
            if not provider:
                mtn_method = self.env.ref('eagle_web_payments.payment_method_mtn')
                airtel_method = self.env.ref('eagle_web_payments.payment_method_airtel')
                mpesa_method = self.env.ref('eagle_web_payments.payment_method_mpesa')
                module = self.env.ref('base.module_eagle_web_payments')
                image_path = get_resource_path('eagle_web_payments', 'static/description', 'icon.png')
                with open(image_path, 'rb') as img_file:
                    image_data = base64.b64encode(img_file.read())
                provider = self.env['payment.provider'].sudo().create({
                    'name': 'Eagle',
                    'code': 'eagle',
                    'allow_tokenization': True,
                    'pending_msg': 'A Confirmation message has been sent to your phone.Please enter the PIN to confirm the payment!',
                    'image_128': image_data,
                    'module_id': module.id,
                    'payment_method_ids': [(6, 0, [mtn_method.id, airtel_method.id, mpesa_method.id])],
                    'company_id': self.company_id.id,
                })
        except Exception as e:
            _logger.info(e)