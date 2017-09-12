# -*- coding: utf-8 -*-

{
    'name': 'Student Exams & Certificates',
    'version': '1.3',
    'summary': 'Exams & Certificates',
    'description': """
        Exams & Certificates for Students
    """,
    'author': 'HashMicro / Janeesh',
    'website': 'www.hashmicro.com',
    'category': 'School Management',
    'sequence': 0,
    'images': [],
    'depends': ['school_management', 'school_enroll'],
    'demo': [],
    'data': [
        'security/ir.model.access.csv',
        'views/student_exam_view.xml',
        'wizard/grade_config_view.xml',
        'views/student_view.xml',
        'sequence.xml',
        'menu.xml'
        ],
    'installable': True,
    'application': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
