{
    'name': 'Services',
    'version': '1.0.0',
    'category': 'Services',
    'summary': 'Company services and pricing management',
    'description': '''
        Services Module
        
        Features:
        - Service catalog management
        - Pricing and duration settings
        - Service categories
        - Integration with appointment system
    ''',
    'author': 'Custom Development',
    'depends': ['base', 'website'],
    'data': [
        'security/ir.model.access.csv',
        'views/service_views.xml',
        'views/service_category_views.xml',
        'data/demo_data.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
