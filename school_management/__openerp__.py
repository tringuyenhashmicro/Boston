# -*- coding: utf-8 -*-

{
    'name': 'School Management',
    'version': '1.81',
    'summary': 'School Management',
    'description': """
        School Management
    """,
    'author': 'HashMicro / Janeesh',
    'website': 'www.hashmicro.com',
    'category': 'School Management',
    'sequence': 0,
    'images': [],
    'depends': ['base', 'portal'],
    'demo': [],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/subject_view.xml',
        'views/class_view.xml',
        'views/session_view.xml',
        'views/student_view.xml',
        'views/teacher_view.xml',
        'menu.xml'
        ],
    'installable': True,
    'application': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
