# -*- coding: utf-8 -*-

{
    'name': 'Student Enrollment',
    'version': '1.7',
    'summary': 'Student Enrollment',
    'description': """
        Student Enrollment
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
        'views/enroll_view.xml',
        'views/class_view.xml',
        'views/student_view.xml',
        'menu.xml',
        'sequence.xml'
        ],
    'installable': True,
    'application': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: