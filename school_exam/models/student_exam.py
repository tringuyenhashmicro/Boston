# -*- coding: utf-8 -*-

from openerp import models, api, _, fields
from openerp.exceptions import Warning

class exam_grade(models.Model):
    _name = 'exam.grade'
    _description = 'Exam Grade'
    _order = 'mark_to desc'
    
    name = fields.Char('Grade Name', required=True)
    mark_from = fields.Integer('From', required=True)
    mark_to = fields.Integer('To', required=True)
    
    @api.returns('self')
    def find(self, mark):
        grade_ids = self.search([('mark_from', '<=', mark), ('mark_to', '>=', mark)])
        return grade_ids and grade_ids[0].id or False
    
class school_exam(models.Model):
    _name = 'school.exam'
    _description = 'School Exam'
    
    name = fields.Char('Name', required=True)
    passing_mark = fields.Integer('Passing Mark', required=True)

class school_test(models.Model):
    _name = 'school.test'
    _description = 'School Test'
    
    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'school.test', context=context)
        return super(school_test, self).create(cr, uid, vals, context=context)
    
    @api.onchange('session_id')
    def _onchange_session(self):
        if self.session_id:
            self.date = self.session_id.date_start
    
    @api.onchange('class_id')
    def _onchange_class(self):
        if self.class_id:
            student_list = []
            for student in self.class_id.student_ids:
                student_list.append((0, 1, {'student_id': student.id}))
            self.student_exam_ids = student_list
        else:
            self.student_exam_ids = False
    
    @api.multi
    def action_completed(self):
        if not self.student_exam_ids:
            raise Warning("Select Students !")
        attended_list = [exam.student_id.id for exam in self.student_exam_ids if exam.attended]
        if not attended_list:
            raise Warning("Atleast one Student should attend !")
        self.state = 'completed'
    
    @api.multi
    def action_result(self):
        for exam in self.student_exam_ids:
            if exam.attended and not exam.grade_id:
                raise Warning("Enter Grade for attended Students !")
        self.state = 'result'
        
    name = fields.Char('Reference')
    exam_id = fields.Many2one('school.exam', 'Test Name', required=True)
    class_id = fields.Many2one('school.class', 'Class', required=True)
    session_id = fields.Many2one('school.session', 'Session', required=True)
    date = fields.Date('Test Date', required=True)
    student_exam_ids = fields.One2many('student.exam', 'test_id', 'Students')
    state = fields.Selection([('started', 'Started'), ('completed', 'Completed'), ('result', 'Result Published')],
        'Status', default='started')

class student_exam(models.Model):
    _name = 'student.exam'
    _description = 'Student Exam'
    
    @api.one
    @api.depends('mark')
    def _find_grade(self):
        self.grade_id = self.env['exam.grade'].find(self.mark)
        
        
    test_id = fields.Many2one('school.test', 'Test')
    student_id = fields.Many2one('school.student', 'Student')
    mark = fields.Integer('Mark')
    grade_id = fields.Many2one('exam.grade', 'Grade', compute=_find_grade)
    attended = fields.Boolean('Attended')
    class_id = fields.Many2one('school.class', 'Class', related='test_id.class_id')
    date = fields.Date(string='Test Date', related='test_id.date')
    session_id = fields.Many2one('school.session', 'Session', related='test_id.session_id')
    result = fields.Char('Result')
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: