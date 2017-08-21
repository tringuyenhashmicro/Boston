from openerp import SUPERUSER_ID
from openerp import tools
import datetime
from datetime import timedelta
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

class res_partner_title(osv.osv):
    _inherit = 'res.partner.title'
    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        if isinstance(ids, (int, long)):
            ids = [ids]
        res = []
        for record in self.browse(cr, uid, ids):
            name = record.shortcut and record.shortcut or record.name
            res.append((record['id'], name))
        return res
    
class school_student(osv.osv):
    _inherit = 'school.student'
    _inherits = {'mail.thread':'message_follower_ids'}
    
    def update_invoice_payment(self, cr, uid, ids=[], context={}):
        inv_obj = self.pool.get('student.invoice')
        payment_obj = self.pool.get('student.payment')
        inv_ids = inv_obj.search(cr, uid, [('bill_to','=',False)])
        payment_ids = payment_obj.search(cr, uid, [('bill_to','=',False)])
        if inv_ids:
            for inv_info in inv_obj.browse(cr, uid, inv_ids):
                inv_obj.write(cr, uid, [inv_info.id], {'bill_to': '%s %s'%(inv_info.student_id.name, inv_info.student_id.l_name and inv_info.student_id.l_name or '')})
        if payment_ids:
            for payment_info in payment_obj.browse(cr, uid, payment_ids):
                payment_obj.write(cr, uid, [payment_info.id], {'bill_to': '%s %s'%(payment_info.student_id.name, payment_info.student_id.l_name and payment_info.student_id.l_name or '')})
        return 1
    
    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        if isinstance(ids, (int, long)):
            ids = [ids]
        res = []
        for record in self.browse(cr, uid, ids):
            name = '%s %s'%(record.name, record.l_name and record.l_name or '')
            res.append((record['id'], name))
        return res
    
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
            for line in record.leave_ids:
                if line.absent_ok or line.leave or line.mc:
                    count += 1
            level = 100
            if record.leave_ids:
                res[record.id] = (1 - (count / len(record.leave_ids))) * 100
                level = ((1 - (count / len(record.leave_ids))) * 100)
            else:
                res[record.id] = 100
            if level < 91:
                values = message_obj.onchange_template_id(cr, uid, ids, template_id, 'comment', 'crm.lead', ids[0])['value']
                values['body'] = '''The Student %s Attendance is below 60'''%(record.name)
                values['partner_ids'] = [(6, 0, user_id)]
                values['subject'] = '''Warning attendance is below 60%'''
                message_id = message_obj.create(cr, uid, values)
                # message_obj.send_mail(cr, SUPERUSER_ID, message_id)
        return res
    
    _columns = {
        'name'       : fields.char('First Name', size=256, required=True),
        'l_name'     : fields.char('Last Name', size=256),
        'std_idd'    : fields.char('Student ID', size=256),
        'image'      : fields.binary('Photo'),
        'birth_date' : fields.date('Date of Birth'),
        'gender'     : fields.selection([('male', 'Male'), ('female', 'Female')], 'Gender'),
        'bill_parent': fields.boolean('Bill to Parent'),
        'is_parent'  : fields.boolean('Is a Parent'),
        'child_ids'  : fields.one2many('school.student', 'parent_id', 'Children'),
        'email'      : fields.char('Email', size=256),
        'user_id'    : fields.many2one('res.users', 'Related User'),
        'oversea_tel': fields.char('Overseas Tel. No', size=256),
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
        'course_id': fields.related('class_id', 'subject_id', type="many2one", relation='school.school', string="Course Name"),
        'school_id': fields.many2one('school.school','Courses Name'),
        'nric_no': fields.char('NRIC/FIN No', size=256),
    }

class student_enroll_line(osv.osv):
    _inherit = 'student.enroll.line'
    _columns = {
    'nric_no': fields.related('student_id', 'nric', type='char', string='NRIC/FIN No'),
    'std_idd': fields.related('student_id', 'std_idd', string='Student ID', type='char'),
    'class_id': fields.related('enroll_id', 'class_id', type='many2one', relation='school.class', string='Intake'),
    'course_id': fields.related('enroll_id', 'course_id', type='many2one', relation='school.school', string='Courses'),
    'date_start': fields.related('enroll_id', 'date_start', type='date', string='Start Date'),
    'date_end': fields.related('enroll_id', 'date_end', type='date', string='End Date'),
    'state': fields.related('enroll_id', 'state', type='selection', string='Status', selection=[('draft', 'Draft'), ('enrolled', 'Enrolled')]),
    }
class school_session(osv.osv):
    _inherit = 'school.session'
    
    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        if isinstance(ids, (int, long)):
            ids = [ids]
        res = []
        for record in self.browse(cr, uid, ids):
            name1 = record.date_start.split(' ')[0].split('-')
            name = '%s/%s/%s'%(name1[2],name1[1],name1[0])
            if record.module_id:
                name += ' - %s'%record.module_id.name
            res.append((record['id'], name))
        return res
    
    def recursive_sessions(self, cr, uid, session, date_start, date_end, number, context=None):
        name = session.name
        if number > 0:
            name = name + ' - ' + str(number)
        session_vals = {
            'name': name,
            'date_start': date_start,
            'date_end': date_end,
            'session_location': session.session_location,
            'class_id': session.class_id.id,
            'module_id': session.module_id and session.module_id.id or 0,
            'teacher_id': session.teacher_id and session.teacher_id.id or 0,
            'classroom_id': session.classroom_id and session.classroom_id.id or 0,
            }
        session_id = self.create(cr, uid, session_vals)
        return session_id
    
    def create(self, cr, uid, vals, context=None):        
        if vals.has_key('date_end') and vals.has_key('date_start'):
            end =  str(vals['date_end']).split(' ')
            end1 = end[0].split('-')
            end2 = end[1].split(':')
            end = datetime.datetime(int(end1[0]), int(end1[1]), int(end1[2]), int(end2[0]), int(end2[1]), int(end2[2]))
            start = str(vals['date_start']).split(' ')
            start1 = start[0].split('-')
            start2 = start[1].split(':')
            start = datetime.datetime(int(start1[0]), int(start1[1]), int(start1[2]), int(start2[0]), int(start2[1]), int(start2[2]))
            tmp = end - start
            if tmp.days < 0:
                raise osv.except_osv('Warning!','Date End can not less than date start!')
        res = super(school_session, self).create(cr, uid, vals, context=context)
        session = self.browse(cr, uid, res)
        pub_day_obj = self.pool.get('hr.holidays')
        if session.recurrency:
            interval = session.interval
            if interval > 0:
                rrule_type = session.rrule_type
                if rrule_type == 'daily':
                    date_start = session.date_start
                    date_end = session.date_end
                    number = session.starting_no
                    if session.end_type == 'count':
                        for s in range(session.count):
                            date_start = datetime.datetime.strptime(str(date_start), "%Y-%m-%d %H:%M:%S")+timedelta(days=interval)
                            if session.exclude_public:
                                pub_ids = pub_day_obj.search(cr, uid, [('public_date','>',str(datetime.datetime.strptime(str(date_start), "%Y-%m-%d %H:%M:%S")-timedelta(days=1))),
                                                                       ('public_date','<',str(datetime.datetime.strptime(str(date_end), "%Y-%m-%d %H:%M:%S")+timedelta(days=1)))])
                                if pub_ids:
                                    for li in pub_day_obj.browse(cr, uid, pub_ids):
                                        
                                        date_startt = str(date_start).split(' ')[0]
                                        #raise osv.except_osv('Warning', str(li.public_date))
                                        # print str(li.public_date), '  ==  ', str(date_startt)
                                        if str(li.public_date) == str(date_startt):
                                            # print 'go to this already !!!!1'
                                            date_start += timedelta(days=1)
                                                                        
                            if session.exclude_weekend:
                                if date_start.weekday() in [5, 6]:
                                    date_start += timedelta(days=1)
                                    if date_start.weekday() in [5, 6]:
                                        date_start += timedelta(days=1)
                            date_end = datetime.datetime.strptime(str(date_end), "%Y-%m-%d %H:%M:%S")+timedelta(days=interval)
                            if session.exclude_weekend:
                                if date_end.weekday() in [5, 6]:
                                    date_end += timedelta(days=1)
                                    if date_end.weekday() in [5, 6]:
                                        date_end += timedelta(days=1)
                            self.recursive_sessions(cr, uid, session, date_start, date_end, number)
                            if number > 0:
                                number += 1
                    else:
                        date_start = datetime.datetime.strptime(str(date_start), "%Y-%m-%d %H:%M:%S")+timedelta(days=interval)
                        date_end = datetime.datetime.strptime(str(date_end), "%Y-%m-%d %H:%M:%S")+timedelta(days=interval)
                        final_date = datetime.datetime.strptime(str(session.final_date), "%Y-%m-%d")+timedelta(days=1)
                        while date_start < final_date:
                            self.recursive_sessions(cr, uid, session, date_start, date_end, number)
                            if session.exclude_public:
                                pub_ids = pub_day_obj.search(cr, uid, [('public_date','>',str(datetime.datetime.strptime(str(date_start), "%Y-%m-%d %H:%M:%S")-timedelta(days=1))),
                                                                       ('public_date','<',str(datetime.datetime.strptime(str(date_end), "%Y-%m-%d %H:%M:%S")+timedelta(days=1)))])
                                if pub_ids:
                                    for li in pub_day_obj.browse(cr, uid, pub_ids):
                                        
                                        date_startt = str(date_start).split(' ')[0]
                                        #raise osv.except_osv('Warning', str(li.public_date))
                                        # print str(li.public_date), '  ==  ', str(date_startt)
                                        if str(li.public_date) == str(date_startt):
                                            # print 'go to this already !!!!1'
                                            date_start += timedelta(days=1)
                            date_start = datetime.datetime.strptime(str(date_start), "%Y-%m-%d %H:%M:%S")+timedelta(days=interval)
                            if session.exclude_weekend:
                                if date_start.weekday() in [5, 6]:
                                    date_start += timedelta(days=1)
                                    if date_start.weekday() in [5, 6]:
                                        date_start += timedelta(days=1)
                            date_end = datetime.datetime.strptime(str(date_end), "%Y-%m-%d %H:%M:%S")+timedelta(days=interval)
                            if session.exclude_weekend:
                                if date_end.weekday() in [5, 6]:
                                    date_end += timedelta(days=1)
                                    if date_end.weekday() in [5, 6]:
                                        date_end += timedelta(days=1)
                            if number > 0:
                                number += 1
        return res
    
from openerp import models, api, _, fields

class fees_category(models.Model):
    _inherit = 'fees.category'
    
    tax_ids = fields.Many2one('account.tax', string='Taxes')
    
class fee_enroll(models.Model):
    _inherit = 'fee.enroll'
    
    @api.onchange('category_id')
    def _onchange_category_id(self):
        if self.category_id:
            self.tax_ids =  self.category_id.tax_ids and [x.id for x in self.category_id.tax_ids] or []
            
    tax_ids = fields.Many2many('account.tax', 'fee_enroll_tax_rel', 'fee_id', 'tax_id', string='Taxes')
                    
class student_enroll(models.Model):
    _inherit = 'student.enroll'

    @api.one
    @api.depends('line_ids')
    def get_attendance_line(self):
        result = []
        if self.line_ids:
            for line in self.line_ids:
                result += self.env['student.attendance.line'].search([('student_id','=',line.student_id.id)])
        self.leave_ids = [i.id for i in result]      
        
    stdidd = fields.Char(string='Student ID', size=256, related='line_ids.student_id.std_idd')
    nric = fields.Char('NRIC/FIN', size=256, related='line_ids.student_id.nric')
    fullname = fields.Many2one('school.student', related='line_ids.student_id', string='Full Name')
    leave_ids = fields.Many2many('student.attendance.line', compute=get_attendance_line)
    
    @api.depends('line_ids')
    @api.onchange('line_ids')
    def _onchange_line_ids(self):
        if self.line_ids:
            self.nric =  str([x.nric_no for x in self.line_ids])
            self.fullname = str(['%s %s'%(x.student_id.name,x.student_id.l_name) for x in self.line_ids])
    
    @api.onchange('class_id')
    def _onchange_class_id(self):
        if self.class_id:
            self.date_start =  self.class_id.start_date and self.class_id.start_date or ''
            self.date_end =  self.class_id.end_date and self.class_id.end_date or ''    

class SchoolClassroom(models.Model):
    _name = 'school.classroom'
    name = fields.Char('Classroom')

class SchoolSession(models.Model):
    _inherit = 'school.session'
    
    name = fields.Char('Session Name', default='Session Name')
    classroom_id = fields.Many2one('school.classroom', string='Classroom')
    module_id = fields.Many2one('school.module', string='Module')
    exclude_weekend = fields.Boolean(string='Exclude Weekend')
    exclude_public = fields.Boolean(string='Exclude Public Holiday')
    
    # @api.onchange('date_end')
    # def _onchange_date_end(self):
        # warning = {}
        # if self.date_end and self.date_start:
            # end =  self.date_end.split(' ')
            # end1 = end[0].split('-')
            # end2 = end[1].split(':')
            # end = datetime.datetime(int(end1[0]), int(end1[1]), int(end1[2]), int(end2[0]), int(end2[1]), int(end2[2]))
            # start = self.date_start.split(' ')
            # start1 = start[0].split('-')
            # start2 = start[1].split(':')
            # start = datetime.datetime(int(start1[0]), int(start1[1]), int(start1[2]), int(start2[0]), int(start2[1]), int(start2[2]))
            # tmp = end - start
            # if tmp.days < 0:
                # raise Warning('Date End can not less than date start!')
                # warning = {'title'     : 'Warning Input Data',
                            # 'message'   : 'Date End can not less than date start!'}
                # self.date_end = ''
        # return {'warning': warning}

class information_source(models.Model):
    _name = 'information.source'
    name = fields.Char('Information Source')

class school_religion(models.Model):
    _name = 'school.religion'
    name = fields.Char('Religion')
        
class SchoolStudent(models.Model):
    _inherit = 'school.student'
    
    @api.one
    def _get_enroll11(self):
        enroll_ids = []
        enroll_line_obj = self.env['student.enroll.line']
        enroll_line_ids = enroll_line_obj.search([('student_id', 'in', self.ids), ('enroll_id.state', '=', 'enrolled')])
        for line in enroll_line_ids:
            enroll_ids.append(line.enroll_id.id)
        self.enroll_ids = self.env['student.enroll'].browse(enroll_ids)
            
    # @api.one
    # def _get_enroll(self):
        # enroll_ids = []
        # enroll_line_obj = self.env['student.enroll.line']
        # enroll_line_ids = enroll_line_obj.search([('student_id', '=', self.id), ('enroll_id.state', '=', 'enrolled')])
        # for line in enroll_line_ids:
            # enroll_ids.append(line.enroll_id.id)
        # self.enroll_ids = enroll_ids
    
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
    
    type_std = fields.Selection([('local','Local'), ('international','International')], string='Type of student')
    leave_ids = fields.One2many('student.attendance.line', 'student_id', 'Leave/MC Summary')
    credit_ids = fields.One2many('student.credit', 'student_id', 'Credits')
    deposit_ids = fields.Many2many('student.deposit.line', 'deposit_student_rel', 'student_id', 'deposit_id', 'Deposit', 
        compute=_get_deposit)
    total_deposit = fields.Float('Total Deposit', compute=_get_deposit)    
    date     = fields.Date('Date')
    payment_ids = fields.One2many('student.payment', 'student_id', 'Payment')
    exam_ids = fields.Many2many('student.exam', 'exam_student_rel', 'student_id', 'exam_id', 'Exams', compute=_get_exam)
    enroll_ids = fields.One2many('student.enroll.line', 'student_id', string='Enrollment')
    assignment_id = fields.One2many('student.assignment', 'student_id', 'Assignment')
    nationality = fields.Many2one('res.country', 'Nationality')
    nric = fields.Char('NRIC/FIN No', size=256)
    religion = fields.Many2one('school.religion', string='Religion')
    married = fields.Selection([('single', 'Single'),
                                ('married', 'Married')], string='Marital Status')
    occupation = fields.Char('Occupation', size=256)
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
    pa_nationality = fields.Many2one('res.country', 'Nationality')
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
    
    @api.model
    def get_payment_term(self):
        payment_term_id = self.env['account.payment.term'].search([('name','=','Immediate Payment')])
        payment_term_id = payment_term_id and payment_term_id[0].id or 0
        return payment_term_id
    
    @api.model
    def get_student_name(self):
        if self.student_id:
            return '%s %s'%(self.student_id.name,self.student_id.l_name)
        return ''
        
    class_id = fields.Many2one('school.class', string='Intake', required=False)
    insu_poli = fields.Char('Insurance Policy No', size=256)
    remarks = fields.Text('Remarks')
    payment_term_id = fields.Many2one('account.payment.term', 'Payment Term', default=get_payment_term)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=1)
    enroll_no = fields.Char('Enrolment No', size=256)
    src_code = fields.Char('Course Code', size=256)
    special_dip = fields.Char('Specialist Diploma in', size=256)
    cer_issue = fields.Char('Certificate Issued By', size=256)
    qualification = fields.Char('Certification/ Qualification', size=256)
    intake = fields.Many2one('school.class', 'Intake')
    fdate_issue = fields.Date('From')
    tdate_issue = fields.Date('To')
    poli_date1 = fields.Date('Insurance Policy Start Date')
    poli_date2 = fields.Date('Insurance Policy End Date')
    nric_no = fields.Char(related='student_id.nric', string='NRIC/FIN No')
    overpaid_amount = fields.Float('Over Paid Amount')
    payment_line_ids = fields.One2many('student.payment.line', 'inv_id', 'Payments')
    student_id = fields.Many2one('school.student', string='Student', required=False)
    bill_to    = fields.Char('Bill To', size=256, default=get_student_name)
    inv_stdidd = fields.Char(string='Student ID', related='student_id.std_idd')
    
    @api.onchange('student_id')
    @api.depends('student_id')
    def _onchange_student(self):
        if self.student_id:
            self.insu_poli = self.student_id.insu_policy
            self.bill_to = '%s %s'%(self.student_id.name,self.student_id.l_name and self.student_id.l_name or '')
    
    @api.one
    @api.depends('invoice_lines.subtotal', 'invoice_lines.std_invoice_line_tax_id')
    def _compute_amount(self):
        self.untax_amount = sum(line.subtotal for line in self.invoice_lines)
        self.tax_amount = sum(line.subtotal * sum([self.env['account.tax'].browse(l.id).amount for l in line.std_invoice_line_tax_id]) for line in self.invoice_lines if line.std_invoice_line_tax_id) or 0
        self.amount_total = self.untax_amount + self.tax_amount
        
    @api.one
    @api.depends('invoice_lines.quantity', 'invoice_lines.price_unit', 'invoice_lines.subtotal')
    def _amount_total(self):
        self.amount_balance = sum(line.subtotal for line in self.invoice_lines) + (sum(line.subtotal * sum([self.env['account.tax'].browse(l.id).amount for l in line.std_invoice_line_tax_id]) for line in self.invoice_lines if line.std_invoice_line_tax_id) or 0) - self.amount_paid
        if self.amount_paid > (self.untax_amount + self.tax_amount):
            self.overpaid_amount = self.amount_paid - (self.untax_amount + self.tax_amount)
        else:
            self.overpaid_amount = 0
    
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
            
    @api.multi
    def make_refund(self):
        copy_invoice = False
        for record in self:
            copy_invoice = record.copy(default={'refund_ok': True,
                                                'name'     : '/',
                                                'invoice_id': record.id})
            for lines in record.invoice_lines:
                lines.copy(default={'invoice_id': copy_invoice.id,})
            record.invoice_id = copy_invoice.id
        return {
            'name': 'Refund Invoice',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'student.invoice',
            'res_id'   : copy_invoice and copy_invoice.id or False,
            'target': 'current',
        }
        
        
student_invoice()

class student_payment_line(models.Model):
    _inherit = 'student.payment.line'
    
    inv_date   = fields.Date(string='Invoice Date', related='inv_id.date')
    inv_std    = fields.Many2one('school.student', string='Student / Bill To', related='inv_id.student_id')
    inv_stdidd = fields.Char(string='Student ID', related='inv_id.student_id.std_idd')
    inv_state  = fields.Selection(string='Status', related='inv_id.state', selection=[('draft', 'Draft'), ('open', 'Open'), ('paid', 'Paid'), ('cancel', 'Cancelled')])
    
    @api.depends('invoice_amount','amount')
    @api.multi
    def get_balance(self):
        for rc in self:
            paid_amount = 0.00
            exist_ids = self.env['student.payment.line'].search([('inv_id','=',rc.inv_id.id),('id','<',rc.id)])
            if exist_ids:
                paid_amount = sum([x.amount for x in self.env['student.payment.line'].browse([i.id for i in exist_ids])])
            if rc.invoice_amount and rc.amount:
                rc.balance = round(round(rc.invoice_amount,3) - round(rc.amount,3) - round(paid_amount,3),3)
            else:
                rc.balance = round(round(rc.invoice_amount,3) - round(paid_amount,3),3)
        
    balance = fields.Float('Balance', compute=get_balance)
    @api.multi
    def print_report(self):        
        data = self.read()[0]
        partner_ids = []
        if self.payment_id:
            partner_ids = [self.payment_id.id]
        data['docids'] = partner_ids
        data['model'] = 'student.payment'
        #    Get report from action and print in the wizard
        act = self.env['report'].get_action(self, 'boston_modifier_status.report_receipt_receipt', data=data)
        return act


class SchoolClass(models.Model):
    _inherit = 'school.class'
    
    @api.multi
    def get_module_id(self):
        for rc in self.browse(self.ids):
            if rc.subject_id:
                if rc.subject_id.shool_module_ids:
                    rc.module_id = rc.subject_id.shool_module_ids[0].id
                    rc.module_id1 = rc.subject_id.shool_module_ids[0].id
    
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    en_start = fields.Date('Enrolment Start Date')
    en_end = fields.Date('Enrolment End Date')
    full_time = fields.Boolean('Full Time')
    part_time = fields.Boolean('Part Time')
    module_id1 = fields.Many2one('school.module', string='Module', compute=get_module_id)
    module_id = fields.Many2one('school.module', string='Module')
    
    @api.onchange('full_time')
    def _onchange_full_time(self):
        if self.full_time:
            self.part_time = False
            
    @api.onchange('part_time')
    def _onchange_part_time(self):
        if self.part_time:
            self.full_time = False
    
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
    
    @api.depends('course_id','class_id','session_id')
    @api.onchange('course_id','class_id','session_id')
    def _onchange_session_id(self):
        if self.course_id and self.class_id and self.session_id:
            attendance_ids = []
            if self.class_id.student_ids:
                for std in self.class_id.student_ids:
                    attendance_ids.append({'student_id': std.id,
                                                'present_ok': False,
                                                'absent_ok':  False,
                                                'leave':      False,
                                                'mc':         False})
            self.attendance_ids = attendance_ids
    
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
    
    passport = fields.Char(string='Passport No', related='student_id.passport_no')
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
    code = fields.Char('Module Code', size=256)
    description = fields.Text('Description')
    theory_ok = fields.Boolean('Theory')
    practical_ok = fields.Boolean('Practical')
    prerequisite = fields.Many2one('school.module', string='Prerequisite')
    shool_course_ids = fields.Many2many('school.school', 'school_school_module_rel', 'module_id', 'school_id', string='Courses')
    
    # @api.onchange('theory_ok')
    # def _onchange_theory_ok(self):
        # if self.theory_ok:
            # self.practical_ok = False
            
    # @api.onchange('practical_ok')
    # def _onchange_practical_ok(self):
        # if self.practical_ok:
            # self.theory_ok = False
    
class FeeEnroll(models.Model):
    _inherit = 'fee.enroll'
    course_id = fields.Many2one('school.school', 'Course')
    
class school_school(models.Model):
    _inherit = 'school.school'
    code = fields.Char('Course Code', size=128)
    cer_ib = fields.Char('Certificate Issued by', size=256)
    cer_quali = fields.Char('Certification/Qualification', size=256)
    entry_req = fields.Text('Entry Requirement')
    course_type = fields.Selection(selection=[('Bachelor', 'Bachelor'), ('Diploma (Articulation)', 'Diploma (Articulation)'), ('Diploma (Non - Articulation)', 'Diploma (Non - Articulation)')], string='Course Type')
    shool_module_ids = fields.Many2many('school.module', 'school_school_module_rel', 'school_id', 'module_id', string='Module')
    enroll_fee_ids = fields.One2many('fee.enroll', 'course_id', 'First Enrollment')
    
    
class StudentInvoiceLine(models.Model):
    _inherit = 'student.invoice.line'
    
    @api.model
    def get_student(self):
        result = 0
        context = self._context
        if context.has_key('student_id'):
            result = context['student_id']
        return result
    
    @api.onchange('cunit_price')
    @api.depends('cunit_price')
    def _onchange_cunit_price(self):
        if self.cunit_price:
            if self.cunit_price.isdigit():
                self.price_unit = eval(self.cunit_price)
            else:
                self.price_unit = 0
        else:
            self.price_unit = 0
    
    cunit_price = fields.Char('Unit Price', size=256)
    student_id = fields.Many2one('school.student', 'Bill To', default=get_student)
    std_invoice_line_tax_id = fields.Many2many('account.tax',
        'std_invoice_line_tax', 'std_invoice_line_id', 'tax_id',
        string='Taxes', domain=[('parent_id', '=', False)])

#   Using for payment
class StudentPayment(models.Model):
    _inherit = 'student.payment'
    
    student_id = fields.Many2one('school.student', string='Student', required=False)
    bill_to    = fields.Char('Bill To', size=256)
    enroll_no = fields.Char(string='Enroll No', related='payment_lines.inv_id.enroll_no', relation='student.invoice')
    inv_stdidd = fields.Char(string='Student ID', related='student_id.std_idd')
    insu_poli = fields.Char('Insurance Policy No', size=256)
    remarks = fields.Text('Remarks')
    payment_term_id = fields.Many2one('account.payment.term', 'Payment Term')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=1)
        
    @api.onchange('student_id')
    @api.depends('student_id')
    def _onchange_student(self):
        if not self.student_id:
            self.payment_lines = False
            bill_to = self.bill_to
            payment_list = []
            inv_obj = self.env['student.invoice']
            if 'inv_id' in self._context:
                invoice = self.env['student.invoice'].browse(self._context['inv_id'])
                if invoice.refund_ok: self.refund_ok = True
                inv_ids = [invoice]
            else:
                domain = [('bill_to', '=', bill_to), ('state', '=', 'open')]
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
                    # 'session_qty': (inv.amount_balance/inv.amount_total) * inv.session_qty
                    }
                payment_list.append((0, 1, rs))
            self.payment_lines = payment_list
        else:
            student_id = self.student_id.id
            self.parent_id = self.student_id.parent_id.id
            self.payment_lines = False
            bill_to = self.bill_to
            payment_list = []
            inv_obj = self.env['student.invoice']
            if 'inv_id' in self._context:
                invoice = self.env['student.invoice'].browse(self._context['inv_id'])
                if invoice.refund_ok: self.refund_ok = True
                inv_ids = [invoice]
            else:
                domain = ['|',('student_id', '=', student_id),('bill_to', '=', bill_to), ('state', '=', 'open')]
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
                    # 'session_qty': (inv.amount_balance/inv.amount_total) * inv.session_qty
                    }
                payment_list.append((0, 1, rs))
            if payment_list:
                self.payment_lines = payment_list
            self.insu_poli = self.student_id.insu_policy
            self.bill_to = '%s %s'%(self.student_id.name,self.student_id.l_name and self.student_id.l_name or '')

    
            
    @api.multi
    def action_validate(self):
        if self.amount <= 0:
            raise Warning("Enter Paid Amount !")
        if 'inv_id' in self._context:
            inv_id = self._context['inv_id']
            invoice = self.env['student.invoice'].browse(inv_id)
            # if self.amount > invoice.amount_balance:
                # raise Warning("Amount exceeds Balance !")
        else:
            total_amount = 0.0
            # for line in self.payment_lines:
                # total_amount += line.amount
                # # if line.amount > line.balance:
                    # # raise Warning("Amount exceeds Balance !")
            # if total_amount != self.amount:
                 # raise Warning("Line Total should match with Paid Amount !")
        class_list = []
        credit_obj = self.env['student.credit']
        for line in self.payment_lines:
            balance = line.inv_id.amount_balance
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
            if line.amount >= balance:
                line.inv_id.state = 'paid'
                
        if self.name == '/' and not self.refund_ok:
            if self.student_id:
                self.name = self.pool.get('ir.sequence').get(self._cr, self._uid, 'stud.payment')
            else:
                self.name = self.pool.get('ir.sequence').get(self._cr, self._uid, 'stud.payment.bill')
        elif self.name == '/' and self.refund_ok:
            if self.student_id:
                self.name = self.pool.get('ir.sequence').get(self._cr, self._uid, 'refund.payment')
            else:
                self.name = self.pool.get('ir.sequence').get(self._cr, self._uid, 'refund.payment.bill')
        self.state = 'posted'
        
class HrHolidays(models.Model):
    _inherit = 'hr.holidays'

    is_public   = fields.Boolean('Is Public Holiday')
    public_date = fields.Date('Date')
    @api.depends('date_from')
    @api.onchange('date_from')
    def _onchange_date_from(self):
        if self.date_from:
            self.public_date = self.date_from
            
    def create(self, cr, uid, vals, context=None):
        if vals.has_key('is_public'):
            if vals.get('is_public', False):
                vals.update({'public_date': vals['date_from']})
        return super(HrHolidays, self).create(cr, uid, vals, context=context)
    
#   USING FOR REPORT         
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
            'doc_ids': docids and docids or data['docids'],
            'doc_model': 'student.payment',
            'docs': docids and self.env['student.payment'].browse(docids) or self.env['student.payment'].browse(data['docids']),
            # 'time': time,
            # 'Lines': lines_to_display,
            # 'Totals': totals,
            # 'Date': fields.date.today(),
        }
        return self.env['report'].render('boston_modifier_status.report_receipt_receipt', values=docargs)
        
class ReportInvocetaxReceipt1(models.AbstractModel):
    _name = 'report.boston_modifier_status.report_invocetax_receipt1'

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
        return self.env['report'].render('boston_modifier_status.report_invocetax_receipt1', values=docargs)

class ReportReceiptReceipt1(models.AbstractModel):
    _name = 'report.boston_modifier_status.report_receipt_receipt1'

    @api.model
    def render_html(self, docids, data=None):
        docargs = {
            'doc_ids': docids and docids or data['docids'],
            'doc_model': 'student.payment',
            'docs': docids and self.env['student.payment'].browse(docids) or self.env['student.payment'].browse(data['docids']),
            # 'time': time,
            # 'Lines': lines_to_display,
            # 'Totals': totals,
            # 'Date': fields.date.today(),
        }
        return self.env['report'].render('boston_modifier_status.report_receipt_receipt1', values=docargs)
        
#   Report Offered
class ReportOfferLetterDocument(models.AbstractModel):
    _name = 'report.boston_modifier_status.report_offer_letter_document'

    @api.model
    def render_html(self, docids, data=None):
        issue_date = data['issued_date'].split('-')
        issue_dated = datetime.date(int(issue_date[0]), int(issue_date[1]), int(issue_date[2]))
        issue_dated += timedelta(days=14)
        issue_dated = str(issue_dated).split('-')
        docargs = {
            'doc_ids': [data['student_id'][0]],
            'doc_model': 'school.student',
            'docs': self.env['school.student'].browse(data['student_id'][0]),
            'issued_date': '%s/%s/%s'%(issue_date[2],issue_date[1],issue_date[0]),
            'end_date': '%s/%s/%s'%(issue_dated[2],issue_dated[1],issue_dated[0]),
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
        # try:
        #imgkit.from_string(self.env['school.school'].browse(data['course_id']).entry_req, '/boston_modifier_status/static/description/%s.png'%self.env['school.school'].browse(data['course_id']).code)
        # except:
            # pass
        docargs = {
            'doc_ids': [data['student_id'][0]],
            'doc_model': 'school.student',
            'docs': self.env['school.student'].browse(data['student_id'][0]),
            'issued_date': '%s/%s/%s'%(issue_date[2],issue_date[1],issue_date[0]),
            'all': self.env['report.student.contract.wizard'].browse(data['all']),
            'course_id': self.env['school.school'].browse(data['course_id']),
            'fee_enroll': self.env['miscellaneous.fee'].browse(data['fee_enroll']),
            'intake_id': self.env['school.class'].browse(data['course_id']),
            'time': time,
            'fulltime': data['fulltime'],
            'parttime': data['parttime'],
            'install_num': data['install_num'],
            'instart': data['instart'] and '%s/%s/%s'%(data['instart'].split('-')[2],data['instart'].split('-')[1],data['instart'].split('-')[0]) or '',
            'inend': data['inend'] and '%s/%s/%s'%(data['inend'].split('-')[2],data['inend'].split('-')[1],data['inend'].split('-')[0]) or '',
            'cissued_by': data['cissued_by'],
            'ccer_qua': data['ccer_qua'],
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
        
class MiscellaneousFee(models.TransientModel):
    _name = 'miscellaneous.fee'
    
    category_id = fields.Many2one('fees.category', string='Category')
    fee_id = fields.Many2one('fee.config', string='Description')
    tax_ids = fields.Many2many('account.tax', 'miscellaneous_tax_rel', 'miscellaneous_id', 'tax_id', string='Taxes')
    amount = fields.Float(string='Price')
    contract_id = fields.Many2one('report.student.contract.wizard', string='Contract')
        
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

    @api.depends('course_id')
    @api.onchange('course_id')
    def _onchange_course(self):
        if self.course_id:
            self.cissued_by = self.course_id.cer_ib
            self.ccer_qua = self.course_id.cer_quali
            print [{'category_id':x.category_id.id,
                                'fee_id': x.fee_id.id,
                                'tax_ids': [y.id for y in x.tax_ids],
                                'amount': x.amount} for x in self.course_id.enroll_fee_ids if x.category_id.name == 'Miscellaneous Fees']
            self.fee_enroll = [{'category_id':x.category_id.id,
                                'fee_id': x.fee_id.id,
                                'tax_ids': [y.id for y in x.tax_ids],
                                'amount': x.amount} for x in self.course_id.enroll_fee_ids if x.category_id.name == 'Miscellaneous Fees']

    @api.depends('intake')
    @api.onchange('intake')
    def _onchange_intake(self):
        if self.intake:
            self.fulltime = self.intake.full_time
            self.parttime = self.intake.part_time
            self.instart = self.intake.start_date
            self.inend = self.intake.end_date
    
    name = fields.Char('Name', size=256)
    student_id = fields.Many2one('school.student', 'Student Name', default=get_student)
    course_id = fields.Many2one('school.school', 'Course Name')
    fulltime = fields.Boolean('Full Time')
    parttime = fields.Boolean('Part Time')
    intake = fields.Many2one('school.class', 'Intake')
    instart = fields.Date('Intake Start Date')
    inend = fields.Date('Intake End Date')
    cissued_by = fields.Char('Certificate Issued By', size=256)
    ccer_qua = fields.Char('Certificattion/Qualification', size=256)
    issued_date = fields.Date('Date of Issue')
    fee_enroll = fields.One2many('miscellaneous.fee', 'contract_id', string='Miscellaneous Fees')
    
    @api.multi
    def print_report(self):        
        data = self.read()[0]
        partner_ids = []
        if self.name:
            partner_ids = [self.student_id.id]
        data['ids'] = partner_ids
        data['issued_date'] = self.issued_date
        data['course_id'] = self.course_id and self.course_id.id or ''
        data['fee_enroll'] = self.fee_enroll and [x.id for x in self.fee_enroll]
        data['intake_id'] = self.intake and self.intake.id or False
        data['fulltime'] = self.fulltime
        data['parttime'] = self.parttime
        data['instart'] = self.instart
        data['inend'] = self.inend
        data['cissued_by'] = self.cissued_by
        data['ccer_qua'] = self.ccer_qua
        data['all'] = self.ids
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        #   Get Instalment Number
        install_num = 0
        for er in self.intake.enroll_ids:
            if er.stdidd == self.student_id.std_idd:
                for l in er.line_ids:
                    if l.std_idd == self.student_id.std_idd:
                        install_num = l.install_num
                break
        data['install_num'] = install_num
        #    Get report from action and print in the wizard
        act = self.env['report'].get_action(self, 'boston_modifier_status.report_student_contract_document', data=data)
        return act

#   Annual Report
class ReportAnnualReportDocument(models.AbstractModel):
    _name = 'report.boston_modifier_status.report_anual_report'

    @api.one
    def get_highest_course(self, std_id):
        for rc in self.env['school.student'].browse(std_id):
            if rc.enroll_ids:
                for c in rc.enroll_ids:
                    if c.course_id.sequence == max([d.course_id.sequence for d in rc.enroll_ids]):
                        return c.course_id
        return False
    
    @api.model
    def render_html(self, docids, data=None):
            
        docargs = {
            'doc_ids': docids,
            'doc_model': 'school.student',
            'docs': self.env['school.student'].browse(docids),
            'get_highest_course': self.get_highest_course(docids[0]),
        }
        return self.env['report'].render('boston_modifier_status.report_anual_report', values=docargs)
        
#   FPS Report
class ReportFPSReportDocument(models.AbstractModel):
    _name = 'report.boston_modifier_status.report_fps_report'

    @api.model
    def render_html(self, docids, data=None):
            
        docargs = {
            'doc_ids': docids,
            'doc_model': 'school.student',
            'docs': self.env['school.student'].browse(docids),
        }
        return self.env['report'].render('boston_modifier_status.report_fps_report', values=docargs)
        
#   FPS Report
class ReportQuarterlyReportDocument(models.AbstractModel):
    _name = 'report.boston_modifier_status.report_quarterly_report'

    @api.model
    def render_html(self, docids, data=None):
            
        docargs = {
            'doc_ids': docids,
            'doc_model': 'school.student',
            'docs': self.env['school.student'].browse(docids),
        }
        return self.env['report'].render('boston_modifier_status.report_quarterly_report', values=docargs)