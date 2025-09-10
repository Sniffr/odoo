import xmlrpc.client
import logging
_logger = logging.getLogger(__name__)
from odoo.http import request
from odoo.exceptions import ValidationError, UserError
import base64



class EagleConnection:
    def __init__(self, model, method, values) -> None:

        self.model_name = model
        self.method = method
        self.values = values

    def get_env(self,company):
        url = request.httprequest.host_url

        # if url in LIVE_URLS:
        _logger.info("*\n\nCONNECTED TO PAYMENTS LIVE***{}\n\n".format(url))
       
        
        encoded_url = "aHR0cHM6Ly9lYWdsZWtlLmtvbGFwcm8uY29tLw=="  
        encoded_db = "ZWFnbGVrZQ=="  
        
        return {
            "username": company.eagle_user_name,
            "password": company.eagle_api_key,
            "url": base64.b64decode(encoded_url).decode(),
            "db": base64.b64decode(encoded_db).decode()
        }
        
        # else:
        #     _logger.info("*\n\nCONNECTED TO PAYMENTS TEST***{}\n\n".format(url))
        #     raise ValidationError("You are not connected to the live environment.")

        
           
            

    def get_response(self,company):
        data = {}
        try:

            envs = self.get_env(company)
            username = envs['username']
            password = envs['password']
            self.url = envs['url']
            self.db =   envs['db']

            common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
            user_id = common.authenticate(self.db, username, password, {})
            # Creating an XML-RPC object for model operations
            models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')

            # Fetching records from the model
            # print(self.values)  
            data = models.execute_kw(self.db, user_id, password, self.model_name, self.method,self.values, {})
            _logger.exception(str(data))
           
            return data
        except Exception as e:
            # raise ValidationError(e)
            _logger.exception(str(e))
            return {
                'fail':True,
                'reason':e,
            }
        except xmlrpc.client.Fault as e:
            _logger.exception(str(e))
            return {
                'fail':True,
                'reason':e,
            }
      