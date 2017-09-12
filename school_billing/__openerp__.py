# -*- coding: utf-8 -*-

{
    'name': 'Student Billing',
    'version': '1.6',
    'summary': 'Student Billing',
    'description': """
        Student Invoicing and Payments
    """,
    'author': 'HashMicro / Janeesh',
    'website': 'www.hashmicro.com',
    'category': 'School Management',
    'sequence': 0,
    'images': [],
    'depends': ['school_enroll', 'school_attendance'],
    'demo': [],
    'data': [
        'security/ir.model.access.csv',
        'views/student_invoice_view.xml',
        'views/webclient_templates.xml',
        'views/student_payment_view.xml',
        'views/class_view.xml',
        'views/student_view.xml',
        'views/enroll_view.xml',
        'views/fee_config_view.xml',
        'views/res_config_view.xml',
        'views/student_deposit_view.xml',
        'menu.xml',
        'sequence.xml'
        ],
    'installable': True,
    'application': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
