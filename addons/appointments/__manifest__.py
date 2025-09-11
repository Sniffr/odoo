{
    'name': 'Appointments',
    'version': '1.0.0',
    'category': 'Website/Website',
    'summary': 'Appointment booking system with staff management',
    'description': """
        Appointments Module for Odoo
        
        This module allows customers to book appointments with staff members
        who are flagged as "bookable" on the company website.
        
        Features:
        - Staff member management with bookable flag
        - Public website pages for staff listings
        - Staff profile pages with specialization and availability
        - Responsive design for mobile and desktop
        
        Step 1 Implementation:
        - Extend res.partner model for staff members
        - Website controller for staff listings
        - QWeb templates for staff display
        - Public access to staff information
    """,
    'author': 'Devin AI',
    'website': 'https://app.devin.ai',
    'depends': ['base', 'website', 'hr'],
    'data': [
        'views/staff_member_views.xml',
        'security/ir.model.access.csv',
        'views/website_templates.xml',
        'data/demo_data.xml',
    ],
    'demo': [
        'data/demo_data.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
