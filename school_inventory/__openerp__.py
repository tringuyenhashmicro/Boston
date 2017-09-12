# -*- coding: utf-8 -*-

{
    'name': 'Inventory Management',
    'version': '1.0',
    'summary': 'Inventory Management',
    'description': """
        School - Inventory Management
    """,
    'author': 'HashMicro / Janeesh',
    'website': 'www.hashmicro.com',
    'category': 'School Management',
    'sequence': 0,
    'images': [],
    'depends': ['school_management'],
    'demo': [],
    'data': [
        'wizard/product_update_view.xml',
        'views/product_transfer_view.xml',
        'views/product_view.xml',
        'security/ir.model.access.csv',
        'menu.xml',
        'sequence.xml'
        ],
    'installable': True,
    'application': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: