#!/usr/bin/env python3
"""
Upgrade custom_appointments module via Odoo XML-RPC.
Run this from inside the odoo container: python3 /tmp/upgrade_module.py
"""
import xmlrpc.client
import sys

url = 'http://localhost:8069'
db = 'lashes'
username = 'admin'
password = 'admin'

print(f"Connecting to {url} db={db} ...")

try:
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
    uid = common.authenticate(db, username, password, {})
    if not uid:
        # try default admin password from config
        password = 'odoo_password'
        uid = common.authenticate(db, username, password, {})
    if not uid:
        print("Authentication failed. Trying to find the admin password...")
        sys.exit(1)
    print(f"Authenticated as uid={uid}")

    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

    # Find the module
    module_ids = models.execute_kw(db, uid, password, 'ir.module.module', 'search',
                                   [[['name', '=', 'custom_appointments']]])
    print(f"Module IDs: {module_ids}")

    if module_ids:
        # Mark for upgrade
        models.execute_kw(db, uid, password, 'ir.module.module', 'button_immediate_upgrade',
                          [module_ids])
        print("Module upgrade triggered successfully!")
    else:
        print("Module not found!")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

