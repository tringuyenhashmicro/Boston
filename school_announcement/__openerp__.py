# -*- coding: utf-8 -*-

{
    'name': 'School Announcements',
    'version': '1.1',
    'summary': 'School Announcements',
    'description': """
        School Announcements
    """,
    'author': 'HashMicro / Janeesh',
    'website': 'www.hashmicro.com',
    'category': 'School Management',
    'sequence': 0,
    'images': [],
    'depends': ['school_management'],
    'demo': [],
    'data': [
        'security/ir.model.access.csv',
        'views/announcements_view.xml',
        'menu.xml',
        'sequence.xml'
        ],
    'installable': True,
    'application': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: