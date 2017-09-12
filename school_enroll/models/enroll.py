# -*- coding: utf-8 -*-

from openerp import models, api, _, fields

class student_enroll(models.Model):
    _name = 'student.enroll'
    _description = 'Student Enroll'
    _order = 'id desc'
    
    name = fields.Char('Reference')
    class_id = fields.Many2one('school.class', 'Class')
    date_start = fields.Date('Start Date')
    date_end = fields.Date('End Date')
    line_ids = fields.One2many('student.enroll.line', 'enroll_id', 'Students')
    state = fields.Selection([('draft', 'Draft'), ('enrolled', 'Enrolled')], 'Status', default='draft')
    
    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'stud.enroll', context=context) or '/'
        return super(student_enroll, self).create(cr, uid, vals, context=context)
    
    @api.multi
    def action_enroll(self):
        self.state = 'enrolled'

    @api.multi
    def action_batch_enroll(self):
        enroll = self.copy({'state': 'draft'})
        return enroll

class student_enroll_line(models.Model):
    _name = 'student.enroll.line'
    _description = 'Student Enroll Line'
    
    student_id = fields.Many2one('school.student', 'Student')
    enroll_id = fields.Many2one('student.enroll', 'Enroll')
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
