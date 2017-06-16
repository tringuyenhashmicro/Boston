from openerp import SUPERUSER_ID
from openerp import tools
import datetime
import time
from openerp.exceptions import Warning
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from openerp.addons.base.res.res_partner import format_address
from openerp.osv import fields, osv, orm
from openerp.tools.translate import _

class crm_lead(format_address, osv.osv):
    _inherit = "crm.lead"
    
    _columns = {
        'state': fields.selection([('applied', 'Applied'),
                                   ('offered', 'Offered'),
                                   ('accepted','Accepted')], 'Status'),
    }
    _defaults = {
        'state': 'applied',
    }
    def btn_offer(self, cr, uid, ids, context={}):
        model_data = self.pool.get('ir.model.data')
        message_obj = self.pool.get('mail.compose.message')
        stage_id = model_data.get_object_reference(cr, SUPERUSER_ID, 'boston_modifier_status', 'stage_offered')[1]
        template_id = model_data.get_object_reference(cr, SUPERUSER_ID, 'crm', 'email_template_opportunity_reminder_mail')[1]
        self.write(cr, uid, ids, {'stage_id': stage_id,
                                  'state': 'offered'})
        values = message_obj.onchange_template_id(cr, uid, ids, template_id, 'comment', 'crm.lead', ids[0])['value']
        message_id = message_obj.create(cr, uid, values)
        message_obj.send_mail(cr, SUPERUSER_ID, message_id)
        return True
        
    def btn_accept(self, cr, uid, ids, context={}):
        model_data = self.pool.get('ir.model.data')
        stage_id = model_data.get_object_reference(cr, SUPERUSER_ID, 'boston_modifier_status', 'stage_accepted')[1]
        self.write(cr, uid, ids, {'stage_id': stage_id, 'state': 'accepted'})
        for lead_info in self.browse(cr, uid, ids):
            account_id = lead_info.partner_id and lead_info.partner_id.property_account_receivable.id or 0
            journal_id = self.pool.get('account.journal').search(cr, SUPERUSER_ID, [('type', '=', 'sale')])
            journal_id = journal_id and journal_id[0] or 0
            self.pool.get('account.invoice').create(cr, SUPERUSER_ID, {'partner_id': lead_info.partner_id.id, 
                                                                       'account_id': account_id,
                                                                       'journal_id': journal_id})
        return True
    
    def btn_enrol(self, cr, uid, ids, context={}):
        model_data = self.pool.get('ir.model.data')
        stage_id = model_data.get_object_reference(cr, SUPERUSER_ID, 'boston_modifier_status', 'stage_accepted')[1]
        student_obj = self.pool.get('school.student')
        for rc in self.browse(cr, uid, ids):
            student_obj.create(cr, uid, {'email': rc.email_from and rc.email_from or '',
                                         'name' : rc.contact_name and rc.contact_name or '',
                                         'display_name': rc.partner_name and rc.partner_name or '',
                                        }, context={})
        return True
crm_lead()
    
class school_student(osv.osv):
    _name = 'school.student'
    _inherit = ['mail.thread', 'ir.needaction_mixin', 'crm.tracking.mixin']
    
    def onchange_birthday(self, cr, uid, ids, birth_date):
        if birth_date:
            cur_date = datetime.date.today()
            cur_date = str(cur_date).split('-')[0]
            birth_date = birth_date.split('-')[0]
            if int(cur_date) - int(birth_date) <= 17:
                return {'value': {'bill_parent': True}}
            else:
                return {'value': {'bill_parent': False}}
        return {'value': {'bill_parent': False}}
    
    def get_current_date(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for record in self.browse(cr, uid, ids):
            res[record.id] = datetime.date.today()
        return res
            
    def get_missing_attendance(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        model_data = self.pool.get('ir.model.data')
        message_obj = self.pool.get('mail.compose.message')
        template_id = model_data.get_object_reference(cr, SUPERUSER_ID, 'boston_modifier_status', 'email_template_missing_three_times')[1]
        group_admin = model_data.get_object_reference(cr, SUPERUSER_ID, 'school_management', 'group_school_admin')[1]
        group_obj = self.pool.get('res.groups')
        user_id = [x.partner_id.id for x in group_obj.browse(cr, SUPERUSER_ID, group_admin).users]
        for record in self.browse(cr, uid, ids):
            count_attendance = 0
            for att_line in record.att_lines:
                if att_line.absent_ok:
                    count_attendance += 1
            if count_attendance >= 3:
                values = message_obj.onchange_template_id(cr, uid, ids, template_id, 'comment', 'school.student', ids[0])['value']
                values['body'] = '''The Student %s is missing for 3 consecutive times'''%(record.name)
                values['partner_ids'] = [(6, 0, user_id)]
                values['subject'] = '''Warning missing for 3 consecutive times'''                
                message_id = message_obj.create(cr, uid, values)
                # message_obj.send_mail(cr, SUPERUSER_ID, message_id)
            res[record.id] = count_attendance
        return res
    
    def get_attendance_rate(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        model_data = self.pool.get('ir.model.data')
        message_obj = self.pool.get('mail.compose.message')
        stage_id = model_data.get_object_reference(cr, SUPERUSER_ID, 'boston_modifier_status', 'stage_offered')[1]
        template_id = model_data.get_object_reference(cr, SUPERUSER_ID, 'crm', 'email_template_opportunity_reminder_mail')[1]
        group_admin = model_data.get_object_reference(cr, SUPERUSER_ID, 'school_management', 'group_school_admin')[1]
        group_obj = self.pool.get('res.groups')
        user_id = [x.partner_id.id for x in group_obj.browse(cr, SUPERUSER_ID, group_admin).users]
        attendance_obj = self.pool.get('student.attendance')
        for record in self.browse(cr, uid, ids):
            level = 100
            class_id = []
            count = 0.00
            attendance_ids = attendance_obj.search(cr, uid, [])
            for attendance in attendance_obj.browse(cr, uid, attendance_ids):
                for line in attendance.attendance_ids:
                    if line.student_id.id == record.id:
                        class_id.append(attendance.class_id)
                        if line.present_ok or line.late_ok or line.leave or line.mc:
                            count += 1
            level = len(class_id) > 0 and (count / len(class_id) * 100) or 0
            res[record.id] = level
            if level < 91:
                values = message_obj.onchange_template_id(cr, uid, ids, template_id, 'comment', 'crm.lead', ids[0])['value']
                values['body'] = '''The Student %s Attendance is below 60'''%(record.name)
                values['partner_ids'] = [(6, 0, user_id)]
                values['subject'] = '''Warning attendance is below 60%'''
                message_id = message_obj.create(cr, uid, values)
                # message_obj.send_mail(cr, SUPERUSER_ID, message_id)
        return res
    
    _columns = {
        'name'  : fields.char('First Name', size=256, required=True),
        'l_name': fields.char('Last Name', size=256),
        'image' : fields.binary('Photo'),
        'birth_date' : fields.date('Date of Birth'),
        'gender'     : fields.selection([('male', 'Male'), ('female', 'Female')], 'Gender'),
        'bill_parent': fields.boolean('Bill to Parent'),
        'is_parent'  : fields.boolean('Is a Parent'),
        'child_ids'  : fields.one2many('school.student', 'parent_id', 'Children'),
        'email'      : fields.char('Email', size=256),
        'user_id'    : fields.many2one('res.users', 'Related User'),
        'parent_id': fields.many2one('school.student', 'Parent', domain=[('is_parent', '=', True)]),
        'state' : fields.selection([('progressed','Progressed'),
                              ('graduated', 'Graduated'),
                              ('completed', 'Completed'),
                              ('withdrawn', 'Withdrawn'),
                              ('expelled', 'Expelled')], string='Status'),
        'wk_pass_issue': fields.date('Work Pass Issue Date'),
        'wk_pass_exp': fields.date('Work Pass Expiry Date'),
        'employer': fields.char('Employer', size=256),
        'att_rate': fields.function(get_attendance_rate, string='Attendance Rate', method=True, type='float'),
        'att_lines': fields.one2many('student.attendance.line', 'student_id', 'Attendance Lines'),
        'current_date' : fields.function(get_current_date, string='Current Date', method=True, type='date'),
        'count_missing': fields.function(get_missing_attendance, string='Consecutive Days', method=True, type='float'),
    }
    
    def write(self, cr, uid, ids, vals, context=None):
        res = super(school_student, self).write(cr, uid, ids, vals, context=context)
        for student in self.browse(cr, uid, ids):
            if student.is_parent or not 'no_user' in context:
                if student.user_id:
                    student.user_id.write({'name': student.name, 'email': student.email})
                else:
                    user_id = self.pool.get('res.users').create(cr, uid, {
                        'name': student.name,
                        'login': student.email
                        }) 
                    student.write({'user_id': user_id})
        return res
    
    def create(self, cr, uid, vals, context=None):
        student_id = super(school_student, self).create(cr, uid, vals, context=context)
        student = self.browse(cr, uid, student_id)
        # Add group student for user
        obj_data = self.pool.get('ir.model.data')
        student_group = obj_data.get_object_reference(cr, uid, 'school_management', 'group_school_student')
        student_group = student_group and student_group[1] or 0        
        if student.is_parent or not 'no_user' in context or not vals.has_key('user_id'):
            user_obj = self.pool.get('res.users')
            user_id = user_obj.create(cr, uid, {
                    'name': student.name,
                    'login': student.email,
                    'no_share': True,
                    'groups_id': [(6, 0, [student_group])] 
                    })
            student.write({'user_id': user_id})
            groups = []
            dataobj = self.pool['ir.model.data']
            dummy,group_id = dataobj.get_object_reference(cr, SUPERUSER_ID, 'base', 'group_portal')
            groups.append(group_id)
            if student.is_parent:
                dummy,group_id = dataobj.get_object_reference(cr, SUPERUSER_ID, 'school_management', 'group_school_parent')
                groups.append(group_id)
            else:
                dummy,group_id = dataobj.get_object_reference(cr, SUPERUSER_ID, 'school_management', 'group_school_student')
                groups.append(group_id)
            user_obj.write(cr, uid, [user_id], {'groups_id': [(6, 0, groups)]})
        return student_id
    
school_student()

class hr_employee(osv.osv):
    _inherit = 'hr.employee'

    def get_current_date(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for record in self.browse(cr, uid, ids):
            res[record.id] = datetime.date.today()
        return res
        
    def get_attendance_rate(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        model_data = self.pool.get('ir.model.data')
        message_obj = self.pool.get('mail.compose.message')
        stage_id = model_data.get_object_reference(cr, SUPERUSER_ID, 'boston_modifier_status', 'stage_offered')[1]
        template_id = model_data.get_object_reference(cr, SUPERUSER_ID, 'crm', 'email_template_opportunity_reminder_mail')[1]
        group_admin = model_data.get_object_reference(cr, SUPERUSER_ID, 'school_management', 'group_school_admin')[1]
        group_obj = self.pool.get('res.groups')
        user_id = [x.partner_id.id for x in group_obj.browse(cr, SUPERUSER_ID, group_admin).users]
        attendance_obj = self.pool.get('teacher.attendance')
        for record in self.browse(cr, uid, ids):
            level = 100
            class_id = []
            count = 0.00
            attendance_ids = attendance_obj.search(cr, uid, [])
            for attendance in attendance_obj.browse(cr, uid, attendance_ids):
                for line in attendance.attendance_ids:
                    if line.teacher_id.id == record.id:
                        class_id.append(attendance.class_id)
                        if line.present_ok:
                            count += 1
            level = len(class_id) > 0 and (count / len(class_id) * 100) or 0
            res[record.id] = level
            if level < 91:
                values = message_obj.onchange_template_id(cr, uid, ids, template_id, 'comment', 'crm.lead', ids[0])['value']
                values['body'] = '''The Teacher %s Attendance is below 60'''%(record.name)
                values['partner_ids'] = [(6, 0, user_id)]
                values['subject'] = '''Warning attendance is below 60%'''
                message_id = message_obj.create(cr, uid, values)
                message_obj.send_mail(cr, SUPERUSER_ID, message_id)
        return res
    _columns = {
        'name' : fields.char('Teacher Name', size=256, required=True),
        'email': fields.char('Email', size=256),
        'user_id': fields.many2one('res.users', 'Related User'),
        'att_rate': fields.function(get_attendance_rate, string='Attendance Rate', method=True, type='float'),
        'att_lines': fields.one2many('teacher.attendance.line', 'teacher_id', 'Attendance Lines'),
        'current_date': fields.function(get_current_date, string='Current Date', method=True, type='date'),
    }
    
    # def write(self, cr, uid, ids, vals, context=None):
        # res = super(school_teacher, self).write(cr, uid, ids, vals, context=context)
        # for teacher in self.browse(cr, uid, ids):
            # if teacher.user_id:
                # teacher.user_id.write({'name': teacher.name, 'email': teacher.email})
            # else:
                # user_id = self.pool.get('res.users').create(cr, uid, {
                    # 'name': teacher.name,
                    # 'login': teacher.email
                    # }) 
                # teacher.write({'user_id': user_id})
        # return res
    
    def create(self, cr, uid, vals, context=None):
        user_obj = self.pool.get('res.users')
        user_id = user_obj.create(cr, uid, {
                'name': vals['name'],
                'login': vals['work_email'],
                })
        if not vals.has_key('resource_id'):
            resource_id = self.pool.get('resource.resource').create(cr, uid, {'name': vals['name'],
                                                                 'resource_type': 'user',
                                                                 'user_id': user_id,
                                                                 'time_efficiency': 1})
            vals.update({'resource_id': resource_id})
        vals.update({'user_id': user_id})
        teacher_id = super(hr_employee, self).create(cr, uid, vals)
        groups = []
        dataobj = self.pool.get('ir.model.data')
        dummy,group_id = dataobj.get_object_reference(cr, SUPERUSER_ID, 'base', 'group_portal')
        groups.append(group_id)
        dummy,group_id = dataobj.get_object_reference(cr, SUPERUSER_ID, 'school_management', 'group_school_teacher')
        groups.append(group_id)
        user_obj.write(cr, uid, [user_id], {'groups_id': [(6, 0, groups)]})
        return teacher_id
    
    
hr_employee()

class student_enroll(osv.osv):
    _inherit = 'student.enroll'
    _columns = {
        'course_id': fields.related('class_id', 'subject_id', type="many2one", relation='school.subject', string="Course Name"),
    }

from openerp import models, api, _, fields

class SchoolClassroom(models.Model):
    _name = 'school.classroom'
    name = fields.Char('Classroom')

class SchoolSession(models.Model):
    _inherit = 'school.session'
    
    name = fields.Char('Session Name', default='Session Name')
    classroom_id = fields.Many2one('school.classroom', string='Classroom')
    module_id = fields.Many2one('school.module', string='Module')

class information_source(models.Model):
    _name = 'information.source'
    name = fields.Char('Information Source')

class school_religion(models.Model):
    _name = 'school.religion'
    name = fields.Char('Religion')
    
class SchoolStudent(models.Model):
    _inherit = 'school.student'
    
    @api.one
    def _get_enroll(self):
        enroll_ids = []
        enroll_line_obj = self.env['student.enroll.line']
        enroll_line_ids = enroll_line_obj.search([('student_id', '=', self.id), ('enroll_id.state', '=', 'enrolled')])
        for line in enroll_line_ids:
            enroll_ids.append(line.enroll_id.id)
        self.enroll_ids = enroll_ids
    
    @api.one
    def _get_exam(self):
        exam_obj = self.env['student.exam']
        exam_ids = exam_obj.search([('student_id', '=', self.id), ('test_id.state', '=', 'result'), ('attended', '=', True)])
        exam_ids = [exam.id for exam in exam_ids]
        self.exam_ids = exam_ids
    
    @api.one
    def _get_deposit(self):
        deposit_ids, total_deposit = [], 0.0
        deposit_line_obj = self.env['student.deposit.line']
        if self.is_parent:
            deposit_line_ids = deposit_line_obj.search([
                ('student_id', 'child_of', self.id), ('deposit_id.state', '=', 'posted')], order='id desc')
        else:
            deposit_line_ids = deposit_line_obj.search([
                ('student_id', '=', self.id), ('deposit_id.state', '=', 'posted')], order='id desc')
        for line in deposit_line_ids:
            deposit_ids.append(line.id)
            total_deposit += line.amount
        self.deposit_ids = deposit_ids
        self.total_deposit = total_deposit
    
    @api.one
    def _get_age(self):
        result = 0
        today = datetime.date.today()
        if self.birth_date:
            tmp = self.birth_date
            tmp = str(tmp).split('-')
            today = str(today).split('-')
            result = int(today[0]) - int(tmp[0])
        self.age = result
        
    credit_ids = fields.One2many('student.credit', 'student_id', 'Credits')
    deposit_ids = fields.Many2many('student.deposit.line', 'deposit_student_rel', 'student_id', 'deposit_id', 'Deposit', 
        compute=_get_deposit)
    total_deposit = fields.Float('Total Deposit', compute=_get_deposit)    
    date     = fields.Date('Date')
    payment_ids = fields.One2many('student.payment', 'student_id', 'Payment')
    exam_ids = fields.Many2many('student.exam', 'exam_student_rel', 'student_id', 'exam_id', 'Exams', compute=_get_exam)
    enroll_ids = fields.Many2many('student.enroll', 'enroll_student_rel', 'student_id', 'enroll_id', 'Enrollment', 
        compute=_get_enroll)
    assignment_id = fields.One2many('student.assignment', 'student_id', 'Assignment')
    nationality = fields.Char('Nationality')
    nric = fields.Char('NRIC/Fin No', size=256)
    religion = fields.Many2one('school.religion', string='Religion')
    married = fields.Selection([('single', 'Single'),
                                ('married', 'Married')], string='Marital Status')
    occupation = fields.Text('Occupation')
    address = fields.Text('Singapore Adress')
    home_tel = fields.Char('Home Tel. No', size=256)
    office_tel = fields.Char('Office Tel. No', size=256)
    handfone = fields.Char('Handphone No')
    emer_name = fields.Char('Name')
    relationship = fields.Char('Relationship', size=256)
    emer_addres  = fields.Text('Address')
    emer_ocupation = fields.Text('Occupation')
    emer_hometel   = fields.Char('Home Tel. No', size=256)
    emer_office_tel = fields.Char('Office Tel. No', size=256)
    emer_handfone = fields.Char('Handphone No')
    emer_email = fields.Char('Email')
    # Add in Information tab
    age = fields.Float('Age', compute=_get_age)
    insu_policy = fields.Char(string='Insurance Policy No', size=256)
    passport_no = fields.Char('Passport No', size=256)
    oversea_add = fields.Text('Overseas Address')
    pass_issue = fields.Date('Student Pass Issue Date')
    pass_exp = fields.Date('Student Pass Expiry Date')
    src_info = fields.Many2one('information.source', string='Information Source')
    crs_consul = fields.Many2one('res.users', string='Course Consultant')
    date_progressed = fields.Date('Progressed')
    date_completed = fields.Date('Completed')
    date_graduated = fields.Date('Graduated')
    date_withdrawn = fields.Date('Withdrawn')
    date_expelled = fields.Date('Expelled')
    # Add Parent Particulars tab
    pa_fullname = fields.Char('Full Name', size=256)
    pa_nationality = fields.Char('Nationality', size=256)
    pa_nric = fields.Char('NRIC/Passport No', size=256)
    pa_address = fields.Text('Address')
    pa_poscode = fields.Char('Postal Code', size=256)
    pa_relation = fields.Char('Relationship', size=256)
    pa_occupation = fields.Char('Occupation', size=256)
    pa_office_tel = fields.Char('Office Tel. No', size=256)
    pa_handphone = fields.Char('Handphone No', size=256)
    pa_email = fields.Char('Email', size=256)
    title_id = fields.Many2one('res.partner.title', 'Title')
    blk = fields.Char('Blk', size=256)
    street = fields.Char('street', size=256)
    unit = fields.Char('Unit', size=256)
    country_id = fields.Many2one('res.country', 'Country')
    postcode = fields.Char('Postal Code', size=256)
    
class teacher_attendance(models.Model):
    _name = 'teacher.attendance'
    _description = 'Student Attendance'
    _order = 'id desc'
    
    name = fields.Char('Reference')
    subject_id = fields.Many2one('school.subject', 'Subject')
    course_id = fields.Many2one('school.school', 'Course Name')
    class_id = fields.Many2one('school.class', 'Class')
    session_id = fields.Many2one('school.session', 'Session')
    attendance_ids = fields.One2many('teacher.attendance.line', 'attendance_id', 'Attendance Lines')
    state = fields.Selection([('draft', 'Draft'), ('posted', 'Validated')], 'Status', default='draft')
    
    
    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'stud.att', context=context) or '/'
        return super(teacher_attendance, self).create(cr, uid, vals, context=context)
    
    @api.multi
    def action_attendance_details(self):
        attendance_line_obj = self.env['student.attendance.line']
        existing_stud = {}
        for attendance in self.attendance_ids:
            existing_stud.update({attendance.student_id.id: attendance})
        for student in self.class_id.student_ids:
            if student.id in existing_stud.keys():
                existing_stud[student.id].write({'gender': student.gender})
            else:
                attendance_line_obj.create({
                    'student_id': student.id,
                    'gender': student.gender,
                    'attendance_id': self.id
                    })
        return True
            
    @api.multi
    def action_validate(self):
        self.state = 'posted'
        
class teacher_attendance_line(models.Model):
    _name = 'teacher.attendance.line'
    _description = 'Teacher Attendance Line'
    
    @api.one
    @api.depends('attendance_id', 'attendance_id.name', 'attendance_id.subject_id', 'attendance_id.class_id',
        'attendance_id.session_id', 'attendance_id.state', 'attendance_id.course_id')
    def _get_attendance_details(self):
        self.name = self.attendance_id.name
        self.subject_id = self.attendance_id.subject_id.id
        self.class_id = self.attendance_id.class_id.id
        self.session_id = self.attendance_id.session_id.id
        self.state = self.attendance_id.state
        self.course_id = self.attendance_id.course_id
        
    attendance_id = fields.Many2one('teacher.attendance', 'Attendance')
    teacher_id = fields.Many2one('hr.employee', 'Teacher')
    present_ok = fields.Boolean('Present', default=True)
    absent_ok = fields.Boolean('Absent')
    late_ok = fields.Boolean('Late')
    leave = fields.Boolean('Leave')
    mc = fields.Boolean('MC')
    makeup_ok = fields.Boolean('Make-Up')
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], 'Gender')
    remark = fields.Char('Remark')
    credits_deduct = fields.Integer('Credits Deducted')
    name = fields.Char('Reference', compute=_get_attendance_details, store=True)
    subject_id = fields.Many2one('school.subject', 'Subject', compute=_get_attendance_details, store=True)
    course_id = fields.Many2one('school.school', 'Course Name', compute=_get_attendance_details, store=True)
    class_id = fields.Many2one('school.class', 'Class', compute=_get_attendance_details, store=True)
    session_id = fields.Many2one('school.session', 'Session', compute=_get_attendance_details, store=True)
    state = fields.Selection([('draft', 'Draft'), ('posted', 'Validated')], 'Status', default='draft',
        compute=_get_attendance_details, store=True)
    
    @api.onchange('present_ok')
    def _onchange_present(self):
        if self.present_ok:
            self.absent_ok, self.late_ok, self.leave, self.mc, self.makeup_ok = False, False, False, False, False
             
    @api.onchange('absent_ok')
    def _onchange_absent(self):
        if self.absent_ok:
            self.present_ok, self.late_ok, self.leave, self.mc, self.makeup_ok = False, False, False, False, False
      
    @api.onchange('late_ok')
    def _onchange_late(self):
        if self.late_ok:
            self.present_ok, self.leave, self.mc, self.absent_ok, self.makeup_ok = False, False, False, False, False
              
    @api.onchange('makeup_ok')
    def _onchange_makeup(self):
        if self.makeup_ok:
            self.present_ok, self.leave, self.mc, self.absent_ok, self.late_ok = False, False, False, False, False

    @api.onchange('leave')
    def _onchange_leave(self):
        if self.leave:
            self.present_ok, self.mc, self.absent_ok, self.late_ok, self.makeup_ok = False, False, False, False, False
            
    @api.onchange('mc')
    def _onchange_mc(self):
        if self.mc:
            self.present_ok, self.leave, self.absent_ok, self.late_ok, self.makeup_ok = False, False, False, False, False
            
class student_invoice(models.Model):
    _inherit = 'student.invoice'
    
    insu_poli = fields.Char('Insurance Policy No', size=256)
    remarks = fields.Text('Remarks')
    payment_term_id = fields.Many2one('account.payment.term', 'Payment Term')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=1)
    enroll_no = fields.Char('Enrolment No', size=256)
    src_code = fields.Char('Course Code', size=256)
    special_dip = fields.Char('Specialist Diploma in', size=256)
    cer_issue = fields.Char('Certificate Issued By', size=256)
    qualification = fields.Char('Certification/ Qualification', size=256)
    intake = fields.Many2one('school.class', 'Intake')
    fdate_issue = fields.Date('From')
    tdate_issue = fields.Date('To')

    
    @api.onchange('student_id')
    @api.depends('student_id')
    def _onchange_student(self):
        if self.student_id:
            self.insu_poli = self.student_id.insu_policy
    
    @api.one
    @api.depends('invoice_lines.subtotal', 'invoice_lines.std_invoice_line_tax_id')
    def _compute_amount(self):
        self.untax_amount = sum(line.subtotal for line in self.invoice_lines)
        self.tax_amount = sum(line.subtotal * sum([self.env['account.tax'].browse(l.id).amount for l in line.std_invoice_line_tax_id]) for line in self.invoice_lines if line.std_invoice_line_tax_id) or 0
        self.amount_total = self.untax_amount + self.tax_amount
    
    invoice_id = fields.Many2one('student.invoice', string='Invoice Information')
    untax_amount = fields.Float('Untaxed Amount', compute='_compute_amount')
    tax_amount = fields.Float('Tax', compute='_compute_amount')
    tender_amount = fields.Float('Tender Amount') 
    
    @api.multi
    def button_reset_taxes(self):
        for rc in self:
            result = 0
            for line in rc.invoice_lines:
                if line.std_invoice_line_tax_id:
                    result += sum([line.subtotal * sum([self.env['account.tax'].browse(l.id).amount for l in line.std_invoice_line_tax_id])])
            rc.tax_amount = result
            rc.amount_total = rc.untax_amount + rc.tax_amount
        return 1
        
    @api.multi
    def action_validate(self):
        self.state = 'open'
        if self.name == '/' and not self.refund_ok:
            self.name = self.pool.get('ir.sequence').get(self._cr, self._uid, 'stud.invoice')
        elif self.name == '/' and self.refund_ok:
            self.name = self.pool.get('ir.sequence').get(self._cr, self._uid, 'refund.invoice')
        
student_invoice()

class SchoolClass(models.Model):
    _inherit = 'school.class'
    
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    en_start = fields.Date('Enrolment Start Date')
    en_end = fields.Date('Enrolment End Date')
    
class school_announcement(models.Model):
    _name = 'school.announcement'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _description = 'School Announcement'
    _order = 'name desc'
    
    name = fields.Char('Reference')
    title = fields.Char('Title')
    description = fields.Text('Description')
    date_publish= fields.Date('Published Date')
    recipient   = fields.Many2one('school.student', string='Recipients')
    course_id   = fields.Many2one('school.subject', string='Course Name')
    batch_id    = fields.Many2one('school.class', string='Batches Name')
    class_id    = fields.Many2one('school.session', string='Class Name')
    state = fields.Selection([('draft', 'Draft'), ('published', 'Published')], 'Status', default='draft')
    
    def create(self, cr, uid, vals, context=None):
        vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'school.announcement', context=context)
        return super(school_announcement, self).create(cr, uid, vals, context=context)
    
    @api.multi
    def action_publish(self):
        self.state = 'published'
        self.date_publish = time.strftime('%Y-%m-%d')
    
    @api.multi
    def send_mail(self):
        
        return True

class student_attendance(models.Model):
    _inherit = 'student.attendance'
    course_id = fields.Many2one('school.school', 'Course Name')    
        
class student_attendance_line(models.Model):
    _inherit = 'student.attendance.line'
    
    @api.one
    @api.depends('attendance_id', 'attendance_id.name', 'attendance_id.subject_id', 'attendance_id.course_id', 'attendance_id.class_id',
        'attendance_id.session_id', 'attendance_id.state')
    def _get_attendance_details(self):
        self.name = self.attendance_id.name
        self.subject_id = self.attendance_id.subject_id.id
        self.class_id = self.attendance_id.class_id.id
        self.session_id = self.attendance_id.session_id.id
        self.state = self.attendance_id.state
        self.course_id = self.attendance_id.course_id.id
    
    leave = fields.Boolean('Leave')
    mc = fields.Boolean('MC')
    course_id = fields.Many2one('school.school', 'Course Name', compute=_get_attendance_details, store=True)
    
    @api.onchange('leave')
    def _onchange_leave(self):
        if self.leave:
            self.present_ok, self.mc, self.absent_ok = False, False, False
            
    @api.onchange('mc')
    def _onchange_mc(self):
        if self.mc:
            self.present_ok, self.leave, self.absent_ok = False, False, False
            
    @api.onchange('present_ok')
    def _onchange_present(self):
        if self.present_ok:
            self.absent_ok, self.late_ok, self.leave, self.mc = False, False, False, False
             
    @api.onchange('absent_ok')
    def _onchange_absent(self):
        if self.absent_ok:
            self.present_ok, self.late_ok, self.leave, self.mc = False, False, False, False
            
class assignment_grade_config(models.TransientModel):
    _inherit = 'assignment.grade.config'
    
    course_id = fields.Many2one('school.school', 'Course Name')
    assignment_id = fields.Many2one('class.assignment', 'Assignment')
    
class school_prerequisite(models.Model):
    _name = 'school.prerequisite'
    name = fields.Char('Name', size=256)
    description = fields.Text('Prerequisite')
    
    # Add new object module above the course
class school_module(models.Model):
    _name = 'school.module'
    _description = 'School Module'

    name = fields.Char('Module Name', size=256)
    description = fields.Text('Description')
    theory_ok = fields.Boolean('Theory')
    practical_ok = fields.Boolean('Practical')
    prerequisite = fields.Many2one('school.module', string='Prerequisite')
    
    # @api.onchange('theory_ok')
    # def _onchange_theory_ok(self):
        # if self.theory_ok:
            # self.practical_ok = False
            
    # @api.onchange('practical_ok')
    # def _onchange_practical_ok(self):
        # if self.practical_ok:
            # self.theory_ok = False
    
    
class school_school(models.Model):
    _inherit = 'school.school'
    code = fields.Char('Course Code', size=128)
    cer_ib = fields.Char('Certificate Issued by', size=256)
    cer_quali = fields.Char('Certification/Qualification', size=256)
    entry_req = fields.Text('Entry Requirement')
    
class StudentInvoiceLine(models.Model):
    _inherit = 'student.invoice.line'
    std_invoice_line_tax_id = fields.Many2many('account.tax',
        'std_invoice_line_tax', 'std_invoice_line_id', 'tax_id',
        string='Taxes', domain=[('parent_id', '=', False)])

#   Using for payment
class StudentPayment(models.Model):
    _inherit = 'student.payment'
    
    insu_poli = fields.Char('Insurance Policy No', size=256)
    remarks = fields.Text('Remarks')
    payment_term_id = fields.Many2one('account.payment.term', 'Payment Term')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=1)
    
    @api.onchange('student_id')
    @api.depends('student_id')
    def _onchange_student(self):
        if not self.student_id:
            self.payment_lines = False
        if self.student_id:
            student_id = self.student_id.id
            self.parent_id = self.student_id.parent_id.id
            self.payment_lines = False
            payment_list = []
            inv_obj = self.env['student.invoice']
            if 'inv_id' in self._context:
                invoice = self.env['student.invoice'].browse(self._context['inv_id'])
                if invoice.refund_ok: self.refund_ok = True
                inv_ids = [invoice]
            else:
                domain = [('student_id', '=', student_id), ('state', '=', 'open')]
                if 'default_refund_ok' in self._context:
                    domain.append(('refund_ok', '=', True))
                inv_ids = inv_obj.search(domain)
            for inv in inv_ids:
                rs = {
                    'invoice_amount': inv.amount_total,
                    'date': inv.date,
                    'balance': inv.amount_balance,
                    'inv_id': inv.id,
                    'class_id': inv.class_id.id,
                    'amount': inv.amount_balance,
                    'session_qty': (inv.amount_balance/inv.amount_total) * inv.session_qty
                    }
                payment_list.append((0, 1, rs))
            if payment_list:
                self.payment_lines = payment_list
            self.insu_poli = self.student_id.insu_policy
            
    @api.multi
    def action_validate(self):
        if self.amount <= 0:
            raise Warning("Enter Paid Amount !")
        if 'inv_id' in self._context:
            inv_id = self._context['inv_id']
            invoice = self.env['student.invoice'].browse(inv_id)
            if self.amount > invoice.amount_balance:
                raise Warning("Amount exceeds Balance !")
        else:
            total_amount = 0.0
            for line in self.payment_lines:
                total_amount += line.amount
                if line.amount > line.balance:
                    raise Warning("Amount exceeds Balance !")
            if total_amount != self.amount:
                 raise Warning("Line Total should match with Paid Amount !")
        class_list = []
        credit_obj = self.env['student.credit']
        for line in self.payment_lines:
            student_ids = list(set([inv_line.student_id.id for inv_line in line.inv_id.invoice_lines]))
            for student_id in student_ids:
                credit_ids = credit_obj.search([
                    ('class_id', '=', line.class_id.id),
                    ('student_id', '=', student_id),
                    ])
                if not credit_ids:
                    credit_obj.create({'class_id': line.class_id.id, 'student_id': student_id})
            if 'inv_id' in self._context:
                line.amount = self.amount
            paid_amount = line.inv_id.amount_paid + line.amount
            line.inv_id.amount_paid = paid_amount
            if paid_amount == line.inv_id.amount_total:
                line.inv_id.state = 'paid'
                
        if self.name == '/' and not self.refund_ok:
            self.name = self.pool.get('ir.sequence').get(self._cr, self._uid, 'stud.payment')
        elif self.name == '/' and self.refund_ok:
            self.name = self.pool.get('ir.sequence').get(self._cr, self._uid, 'refund.payment')
        self.state = 'posted'
        
class ReportCreditNoteReceipt(models.AbstractModel):
    _name = 'report.boston_modifier_status.report_credit_note_receipt'

    @api.model
    def render_html(self, docids, data=None):
        docargs = {
            'doc_ids': docids,
            'doc_model': 'student.invoice',
            'docs': self.env['student.invoice'].browse(docids),
            # 'time': time,
            # 'Lines': lines_to_display,
            # 'Totals': totals,
            # 'Date': fields.date.today(),
        }
        return self.env['report'].render('boston_modifier_status.report_credit_note_receipt', values=docargs)
        
class ReportInvocetaxReceipt(models.AbstractModel):
    _name = 'report.boston_modifier_status.report_invocetax_receipt'

    @api.model
    def render_html(self, docids, data=None):
        docargs = {
            'doc_ids': docids,
            'doc_model': 'student.invoice',
            'docs': self.env['student.invoice'].browse(docids),
            # 'time': time,
            # 'Lines': lines_to_display,
            # 'Totals': totals,
            # 'Date': fields.date.today(),
        }
        return self.env['report'].render('boston_modifier_status.report_invocetax_receipt', values=docargs)

class ReportReceiptReceipt(models.AbstractModel):
    _name = 'report.boston_modifier_status.report_receipt_receipt'

    @api.model
    def render_html(self, docids, data=None):
        docargs = {
            'doc_ids': docids,
            'doc_model': 'student.payment',
            'docs': self.env['student.payment'].browse(docids),
            # 'time': time,
            # 'Lines': lines_to_display,
            # 'Totals': totals,
            # 'Date': fields.date.today(),
        }
        return self.env['report'].render('boston_modifier_status.report_receipt_receipt', values=docargs)
        
#   Report Offered
class ReportOfferLetterDocument(models.AbstractModel):
    _name = 'report.boston_modifier_status.report_offer_letter_document'

    @api.model
    def render_html(self, docids, data=None):
        issue_date = data['issued_date'].split('-')
        docargs = {
            'doc_ids': [data['student_id'][0]],
            'doc_model': 'school.student',
            'docs': self.env['school.student'].browse(data['student_id'][0]),
            'issued_date': '%s/%s/%s'%(issue_date[2],issue_date[1],issue_date[0]),
            'note': data['note'],
            'course_id': data['course_id'],
            'time': time,
        }
        return self.env['report'].render('boston_modifier_status.report_offer_letter_document', values=docargs)
        
#   Report Contract
class ReportStudentContractDocument(models.AbstractModel):
    _name = 'report.boston_modifier_status.report_student_contract_document'

    @api.model
    def render_html(self, docids, data=None):
        issue_date = data['issued_date'].split('-')
        # raise Warning(str(data))
        docargs = {
            'doc_ids': [data['student_id'][0]],
            'doc_model': 'school.student',
            'docs': self.env['school.student'].browse(data['student_id'][0]),
            'issued_date': '%s/%s/%s'%(issue_date[2],issue_date[1],issue_date[0]),
            'note': data['note'],
            'course_id': data['course_id'],
            'time': time,
        }
        return self.env['report'].render('boston_modifier_status.report_student_contract_document', values=docargs)

class ReportOfferWizard(models.TransientModel):
    _name = 'report.offer.wizard'
    
    @api.model
    def get_student(self):
        result = 0
        context = self._context
        if context.has_key('student_id'):
            result = context['student_id']
        return result
    
    name = fields.Char('Name', size=256)
    student_id = fields.Many2one('school.student', 'Student Name', default=get_student)
    issued_date = fields.Date('ISSUE DATE OF CONTRACT')
    course_id = fields.Many2one('school.school', 'Course Name')
    note = fields.Text('Note')
    
    @api.multi
    def print_report(self):
        data = self.read()[0]
        partner_ids = []
        if self.name:
            partner_ids = [self.student_id.id]
        data['ids'] = partner_ids
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        #    Get report from action and print in the wizard
        act = self.env['report'].get_action(self, 'boston_modifier_status.report_offer_letter_document', data=data)
        return act
        
class ReportStudentContractWizard(models.TransientModel):
    _name = 'report.student.contract.wizard'
    
    @api.model
    def get_student(self):
        result = 0
        context = self._context
        if context.has_key('student_id'):
            result = context['student_id']
        return result
        
    @api.onchange('fulltime')
    def _onchange_fulltime(self):
        if self.fulltime:
            self.parttime = False
    
    @api.onchange('parttime')
    def _onchange_parttime(self):
        if self.parttime:
            self.fulltime = False
    
    name = fields.Char('Name', size=256)
    student_id = fields.Many2one('school.student', 'Student Name', default=get_student)
    issued_date = fields.Date('Issue Date of Contract')
    course_id = fields.Many2one('school.school', 'Course Name')
    fulltime = fields.Boolean('Full Time')
    parttime = fields.Boolean('Part Time')
    intake = fields.Many2one('school.class', 'Intake')
    instart = fields.Date('Intake Start Date')
    inend = fields.Date('Intake End Date')
    cissued_by = fields.Char('Certificate Issued By', size=256)
    ccer_qua = fields.Char('Certificattion/Qualification', size=256)
    issued_date = fields.Date('Date of Issue')
    
    @api.multi
    def print_report(self):        
        data = self.read()[0]
        partner_ids = []
        if self.name:
            partner_ids = [self.student_id.id]
        data['ids'] = partner_ids
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        #    Get report from action and print in the wizard
        act = self.env['report'].get_action(self, 'boston_modifier_status.report_student_contract_document', data=data)
        return act