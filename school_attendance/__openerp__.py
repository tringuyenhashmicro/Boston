# -*- coding: utf-8 -*-

{
    'name': 'Student Attendance',
    'version': '1.7',
    'summary': 'Student Attendance',
    'description': """
        Student Attendance
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
        'views/attendance_view.xml',
        'menu.xml',
        'sequence.xml'
        ],
    'installable': True,
    'application': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: