from openerp import SUPERUSER_ID
from openerp import tools
import datetime
from openerp.osv import fields, osv

class res_language(osv.osv):
    _name = 'res.language'
    _columns = {
        'name': fields.char('Name', size=256),
    }
res_language()

class school_student_education(osv.osv):
    _name = 'school.student.education'
    _columns = {
        'student_id': fields.many2one('school.student', 'Student'),
        'name' : fields.char('Name of Institutions', size=256),
        'country_id': fields.many2one('res.country', 'Country'),
        'language_id': fields.many2one('res.language', 'Language'),
        'from_date': fields.date('From'),
        'to_date': fields.date('To'),
        'qualification': fields.char('Qualification', size=256),
        'obtain': fields.selection([('yes','Yes'),('no','No')], 'Obtained a Pass in English'),
        'grade_obtain': fields.char('Grade Obtained in English', size=256),
    }
school_student_education()

class school_student_history(osv.osv):
    _name = 'school.student.history'
    _columns = {
        'student_id': fields.many2one('school.student', 'Student'),
        'name' : fields.char('Name of Companies', size=256),
        'country_id': fields.many2one('res.country', 'Country'),
        'from_date': fields.date('From'),
        'to_date': fields.date('To'),
        'position': fields.char('Position Held', size=256),
    }
school_student_history()

class school_student(osv.osv):
    _inherit = 'school.student'
    _columns = {
        'education_background': fields.one2many('school.student.education', 'student_id', 'Education Background'),
        'history_id': fields.one2many('school.student.history', 'student_id', 'History'),
        'obtain': fields.boolean(string='Obtained a Pass in English'),
        'grade_obtain': fields.char('Grade Obtained in English', size=256),
    }
school_student()