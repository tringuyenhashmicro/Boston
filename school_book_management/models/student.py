# -*- coding: utf-8 -*-

from openerp import models, api, _, fields

class school_student(models.Model):
    _inherit = 'school.student'
    
    holder_id = fields.Many2one('book.holder', 'Book Holder')
    
    def create(self, cr, uid, vals, context=None):
        student_id = super(school_student, self).create(cr, uid, vals, context=context)
        student = self.browse(cr, uid, student_id)
        if not student.is_parent:
            holder_obj = self.pool.get('book.holder')
            holder_id = holder_obj.create(cr, uid, {
                    'name': student.name,
                    'type': 'student'
                    })
            student.write({'holder_id': holder_id})
        return student_id
    
class school_teacher(models.Model):
    _inherit = 'school.teacher'
    
    holder_id = fields.Many2one('book.holder', 'Book Holder')
    
    def create(self, cr, uid, vals, context=None):
        teacher_id = super(school_teacher, self).create(cr, uid, vals, context=context)
        teacher = self.browse(cr, uid, teacher_id)
        holder_obj = self.pool.get('book.holder')
        holder_id = holder_obj.create(cr, uid, {
                'name': teacher.name,
                'type': 'teacher'
                })
        teacher.write({'holder_id': holder_id})
        return teacher_id
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: