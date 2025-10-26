{
    'name': 'Custom Appointments',
    'version': '1.1.1',
    'category': 'Services',
    'summary': 'Complete appointment booking system with staff, branches, and services',
    'description': '''
        Custom Appointments Module
        
        Features:
        - Staff member management with booking capabilities
        - Branch management for multi-location businesses
        - Service catalog with pricing and categories
        - Staff availability and booking system
        - Appointment booking with calendar integration
        - Email notifications with calendar invites (.ics files)
        - Integration with company structure
        - Automatic conflict detection for manual and website bookings
        - Prevents double booking of staff members
    ''',
    'author': 'Custom Development',
    'depends': ['base', 'hr', 'calendar', 'website', 'mail', 'sms', 'account', 'payment'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/employee_import_wizard_views.xml',
        'wizard/company_import_wizard_views.xml',
        'views/staff_member_views.xml',
        'views/staff_dashboard_views.xml',
        'views/branch_views.xml',
        'views/service_views.xml',
        'views/service_category_views.xml',
        'views/appointment_views.xml',
        'views/website_templates.xml',
        'data/mail_templates.xml',
        'data/cron_jobs.xml',
    ],
    'demo': [
        'data/demo_data.xml',
        'data/services_demo_data.xml',
        'data/appointment_demo_data.xml',
    ],
    'external_dependencies': {
        'python': ['icalendar'],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
