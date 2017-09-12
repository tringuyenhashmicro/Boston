# -*- coding: utf-8 -*-

{
    'name': 'Book Management',
    'version': '1.0',
    'summary': 'Book Management',
    'description': """
        School - Book Management
    """,
    'author': 'HashMicro / Janeesh',
    'website': 'www.hashmicro.com',
    'category': 'School Management',
    'sequence': 0,
    'images': [],
    'depends': ['school_management', 'school_inventory'],
    'demo': [],
    'data': [
        'wizard/book_update_view.xml',
        'views/book_transfer_view.xml',
        'views/book_view.xml',
        'security/ir.model.access.csv',
        'data.xml',
        'sequence.xml',
        'menu.xml'
        ],
    'installable': True,
    'application': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: