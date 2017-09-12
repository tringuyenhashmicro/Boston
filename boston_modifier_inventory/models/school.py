from openerp import SUPERUSER_ID
from openerp import tools
import datetime
from openerp.osv import fields, osv

# class school_module(osv.osv):
    # _inherit = 'school.module'

    # _columns = {
        # 'shool_course_ids': fields.many2many('school.school', 'module_course_rel', 'school_module_id', 'school_school_id', string='Courses', readonly=True),
    # }


# class school_school(osv.osv):
    # _inherit = 'school.school'

    # _columns = {
        # 'shool_module_ids': fields.many2many('school.module', 'module_course_rel', 'school_school_id', 'school_module_id', string='Modules'),
    # }

# class school_session(osv.osv):
    # _inherit = 'school.session'

    # _columns = {
        # 'exclude_weekend': fields.boolean(string='Exclude Weekend'),
    # }