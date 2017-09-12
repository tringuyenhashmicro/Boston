# -*- coding: utf-8 -*-

from openerp import models, api, _, fields

class student_attendance(models.Model):
    _name = 'student.attendance'
    _description = 'Student Attendance'
    _order = 'id desc'
    
    name = fields.Char('Reference')
    subject_id = fields.Many2one('school.subject', 'Subject')
    class_id = fields.Many2one('school.class', 'Class')
    session_id = fields.Many2one('school.session', 'Session')
    attendance_ids = fields.One2many('student.attendance.line', 'attendance_id', 'Attendance Lines')
    state = fields.Selection([('draft', 'Draft'), ('posted', 'Validated')], 'Status', default='draft')
    
    
    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'stud.att', context=context) or '/'
        return super(student_attendance, self).create(cr, uid, vals, context=context)
    
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
    
    # @api.onchange('session_id', 'class_id')
    # def _onchange_session(self):
        # if self.session_id:
            # student_list = []
            # for student in self.class_id.student_ids:
                # student_list.append((0, 1, {'student_id': student.id, 'gender': student.gender}))
            # self.attendance_ids = student_list
        # else:
            # self.attendance_ids = False
            
    @api.multi
    def action_validate(self):
        self.state = 'posted'
        
class student_attendance_line(models.Model):
    _name = 'student.attendance.line'
    _description = 'Student Attendance Line'
    
    @api.one
    @api.depends('attendance_id', 'attendance_id.name', 'attendance_id.subject_id', 'attendance_id.class_id',
        'attendance_id.session_id', 'attendance_id.state')
    def _get_attendance_details(self):
        self.name = self.attendance_id.name
        self.subject_id = self.attendance_id.subject_id.id
        self.class_id = self.attendance_id.class_id.id
        self.session_id = self.attendance_id.session_id.id
        self.state = self.attendance_id.state
        
    attendance_id = fields.Many2one('student.attendance', 'Attendance')
    student_id = fields.Many2one('school.student', 'Student')
    present_ok = fields.Boolean('Present', default=True)
    absent_ok = fields.Boolean('Absent')
    late_ok = fields.Boolean('Late')
    makeup_ok = fields.Boolean('Make-Up')
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], 'Gender')
    remark = fields.Char('Remark')
    credits_deduct = fields.Integer('Credits Deducted')
    name = fields.Char('Reference', compute=_get_attendance_details, store=True)
    subject_id = fields.Many2one('school.subject', 'Subject', compute=_get_attendance_details, store=True)
    class_id = fields.Many2one('school.class', 'Class', compute=_get_attendance_details, store=True)
    session_id = fields.Many2one('school.session', 'Session', compute=_get_attendance_details, store=True)
    state = fields.Selection([('draft', 'Draft'), ('posted', 'Validated')], 'Status', default='draft',
        compute=_get_attendance_details, store=True)
    
    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        res = super(student_attendance_line, self).search(cr, uid, args=args, offset=offset, limit=limit, order=order, context=context)
        user_obj = self.pool.get('res.users')
        admin = user_obj.has_group(cr, uid, 'school_management.group_school_admin')
        teacher = user_obj.has_group(cr, uid, 'school_management.group_school_teacher')
        student = user_obj.has_group(cr, uid, 'school_management.group_school_student')
        parent = user_obj.has_group(cr, uid, 'school_management.group_school_parent')
        ids = []
        if admin:
            return res
        elif teacher:
            class_ids = self.pool.get('school.class').search(cr, uid, [('teacher_id.user_id', '=', uid)])
            args.extend([('class_id', 'in', class_ids)])
            ids = super(student_attendance_line, self).search(cr, uid, args=args, offset=offset, limit=limit, order=order, context=context)
        elif student:
            args.extend([('student_id.user_id', '=', uid)])
            ids = super(student_attendance_line, self).search(cr, uid, args=args, offset=offset, limit=limit, order=order, context=context)
        elif parent:
            student_ids = self.pool.get('school.student').search(cr, uid, [('parent_id.user_id', '=', uid)])
            args.extend([('student_id', 'in', student_ids)])
            ids = super(student_attendance_line, self).search(cr, uid, args=args, offset=offset, limit=limit, order=order, context=context)
        return ids
    
    @api.onchange('student_id')
    def _onchange_student(self):
        if self.student_id:
            self.gender = self.student_id.gender
        else:
            self.gender = ''
    
    @api.onchange('present_ok')
    def _onchange_present(self):
        if self.present_ok:
            self.absent_ok, self.late_ok, self.makeup_ok = False, False, False
             
    @api.onchange('absent_ok')
    def _onchange_absent(self):
        if self.absent_ok:
            self.present_ok, self.late_ok, self.makeup_ok = False, False, False
      
    @api.onchange('late_ok')
    def _onchange_late(self):
        if self.late_ok:
            self.present_ok, self.absent_ok, self.makeup_ok = False, False, False
              
    @api.onchange('makeup_ok')
    def _onchange_makeup(self):
        if self.makeup_ok:
            self.present_ok, self.absent_ok, self.late_ok = False, False, False
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: