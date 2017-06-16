from openerp import SUPERUSER_ID
from openerp import tools
import datetime
from openerp.osv import fields, osv

# class school_teacher(osv.osv):
    # _inherit = 'school.teacher'
    # _columns = {
        # 'employee_id': fields.many2one('hr.employee', 'Employee')
    # }
# school_teacher()

class school_test(osv.osv):
    _inherit = 'school.test'
    _columns = {
        'attachment' : fields.binary('Test File'),
    }
school_test()

class HrEmployee(osv.osv):
    _inherit = 'hr.employee'
    _columns = {
        'type': fields.selection([('teacher', 'Teacher'),
                                 ('employee', 'Employee'),
                                 ('recruitment' ,'Recruitment Agent')], 'Type'),
    }
    _defaults = {
        'type': 'employee',
    }
    # def update_employee_all(self, cr, uid, context=None):
        # teacher_obj  = self.pool.get('hr.employee')
        # employee_obj = self.pool.get('hr.employee')
        # teacher_ids = teacher_obj.search(cr, uid, [('employee_id','=',False)])
        # for record in teacher_obj.browse(cr, uid, teacher_ids):
            # employee_id = employee_obj.create(cr, uid, {  'name'      : record.name and record.name or '',
                                                          # 'work_email': record.email and record.email or '',
                                                          # 'user_id'   : record.user_id and record.user_id.id or 0,
                                                          # 'type'      : 'teacher'})
            # teacher_obj.write(cr, uid, [record.id], {'employee_id': employee_id})

        # return 1
HrEmployee()