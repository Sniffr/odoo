{
    'name': 'Custom Appointments',
    'version': '1.0.0',
    'category': 'Services',
    'summary': 'Staff and branch booking management system',
    'description': '''
        Custom Appointments Module
        
        Features:
        - Staff member management with booking capabilities
        - Branch management for multi-location businesses
        - Staff availability and booking system
        - Integration with company structure
    ''',
    'author': 'Custom Development',
    'depends': ['base', 'website', 'hr'],
    'data': [
        'security/ir.model.access.csv',
        'views/staff_member_views.xml',
        'views/branch_views.xml',
        'data/demo_data.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
