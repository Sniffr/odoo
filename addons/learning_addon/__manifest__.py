{
    'name': 'Learning Addon',
    'version': '1.0.0',
    'category': 'Website',
    'summary': 'Simple learning addon to understand Odoo development',
    'description': '''
        A simple learning addon that demonstrates:
        - Creating a custom model
        - Adding data to the database
        - Displaying data on the website
        - Basic Odoo development concepts
        
        Compatible with Odoo 18.0
    ''',
    'author': 'Learning Developer',
    'depends': ['base', 'website'],
    'data': [
        'security/ir.model.access.csv',
        'views/learning_views.xml',
        'views/website_templates.xml',
        'data/demo_data.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
