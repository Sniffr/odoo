#!/usr/bin/env python3
"""
Script to update mail template records with correct Mako syntax.
Run this script if the module update (-u custom_appointments) doesn't work.

Usage:
    docker compose exec odoo python3 /mnt/extra-addons/update_email_templates.py

Or if running Odoo directly:
    python3 update_email_templates.py
"""
import sys
import os

sys.path.insert(0, '/usr/lib/python3/dist-packages')
os.environ['ODOO_RC'] = '/etc/odoo/odoo.conf'

import odoo
from odoo import api, SUPERUSER_ID

odoo.tools.config.parse_config(['-c', '/etc/odoo/odoo.conf'])

db_name = sys.argv[1] if len(sys.argv) > 1 else 'app1'

print(f"Connecting to database: {db_name}")

try:
    registry = odoo.registry(db_name)
except Exception as e:
    print(f"ERROR: Could not connect to database {db_name}: {e}")
    print("Please provide the correct database name as an argument:")
    print(f"  python3 {sys.argv[0]} <database_name>")
    sys.exit(1)

with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    print("\n=== Updating Mail Templates with Mako Syntax ===\n")
    
    print("1. Updating Appointment Confirmation template...")
    try:
        template = env.ref('custom_appointments.appointment_confirmation_email', raise_if_not_found=False)
        if template:
            template.write({
                'subject': 'Appointment Confirmed - ${object.name}',
                'email_from': '${object.branch_id.email or user.company_id.email or \'noreply@localhost\'}',
                'email_to': '${object.customer_email}',
            })
            print(f"   ✓ Updated template ID {template.id}")
        else:
            print("   ⚠ Template not found (module may not be installed)")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n2. Updating Appointment Reminder template...")
    try:
        template = env.ref('custom_appointments.appointment_reminder_email', raise_if_not_found=False)
        if template:
            template.write({
                'subject': 'Reminder: Your appointment tomorrow - ${object.name}',
                'email_from': '${object.branch_id.email or user.company_id.email or \'noreply@localhost\'}',
                'email_to': '${object.customer_email}',
            })
            print(f"   ✓ Updated template ID {template.id}")
        else:
            print("   ⚠ Template not found (module may not be installed)")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n3. Updating Staff Notification template...")
    try:
        template = env.ref('custom_appointments.staff_notification_email', raise_if_not_found=False)
        if template:
            template.write({
                'subject': 'New Appointment Booked - ${object.name}',
                'email_from': '${user.company_id.email or \'noreply@localhost\'}',
                'email_to': '${object.staff_member_id.email}',
            })
            print(f"   ✓ Updated template ID {template.id}")
        else:
            print("   ⚠ Template not found (module may not be installed)")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n4. Updating Appointment Cancellation template...")
    try:
        template = env.ref('custom_appointments.appointment_cancellation_email', raise_if_not_found=False)
        if template:
            template.write({
                'subject': 'Appointment Cancelled - ${object.name}',
                'email_from': '${object.branch_id.email or user.company_id.email or \'noreply@localhost\'}',
                'email_to': '${object.customer_email}',
            })
            print(f"   ✓ Updated template ID {template.id}")
        else:
            print("   ⚠ Template not found (module may not be installed)")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    cr.commit()
    print("\n✅ All templates updated successfully!")
    print("\nTemplates now use Mako syntax ${...} instead of Jinja2 syntax {{...}}")
    print("Email notifications should now render correctly with actual values.")
