# -*- coding: utf-8 -*-
{
    'name': "boston_modifier_access_right",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Boston Access Right 
    """,

    'author': "Hashmicro / Sang",
    'website': "http://www.hashmicro.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','hr', 'boston_modifier_human_resources','mail','school_management','hr_holidays'],

    # always loaded
    'data': [
        'templates.xml',
        'security/ir.model.access.csv',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],
}