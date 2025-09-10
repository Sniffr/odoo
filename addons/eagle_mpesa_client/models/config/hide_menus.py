from odoo import api, fields, models, Command, _, tools                                       

class Menu(models.Model):
    _inherit = 'ir.ui.menu'

    @api.model
    @tools.ormcache('frozenset(self.env.user.groups_id.ids)', 'debug')
    def _visible_menu_ids(self, debug=False):	
        
        menus = super(Menu,self)._visible_menu_ids(debug)        	

        if not (self.env.user.has_group('base.group_system')) and not self.env.user.company.enable_kola_mpesa:
            menus.discard(self.env.ref("eagle_mpesa_client.menu_sacco_base_root").id)
          
        return menus
