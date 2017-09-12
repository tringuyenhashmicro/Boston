# -*- coding: utf-8 -*-

{
    'name': 'Student Assignment',
    'version': '1.4',
    'summary': 'Student Assignment',
    'description': """
        Student Assignment
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
        'views/assignment_view.xml',
        'wizard/grade_config_view.xml',
        'menu.xml',
        'sequence.xml'
        ],
    'installable': True,
    'application': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: