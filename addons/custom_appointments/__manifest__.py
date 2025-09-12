{
    'name': 'Custom Appointments',
    'version': '1.0.0',
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
        - Integration with company structure
    ''',
    'author': 'Custom Development',
    'depends': ['base', 'hr', 'calendar'],
    'data': [
        'security/ir.model.access.csv',
        'views/staff_member_views.xml',
        'views/branch_views.xml',
        'views/service_views.xml',
        'views/service_category_views.xml',
        'views/appointment_views.xml',
        'data/demo_data.xml',
        'data/services_demo_data.xml',
        'data/appointment_demo_data.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
