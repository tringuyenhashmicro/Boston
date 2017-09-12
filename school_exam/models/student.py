# -*- coding: utf-8 -*-

from openerp import models, api, _, fields

class school_class(models.Model):
    _inherit = 'school.student'
    
    @api.one
    def _get_exam(self):
        exam_obj = self.env['student.exam']
        exam_ids = exam_obj.search([('student_id', '=', self.id), ('test_id.state', '=', 'result'), ('attended', '=', True)])
        exam_ids = [exam.id for exam in exam_ids]
        self.exam_ids = exam_ids
        
    exam_ids = fields.Many2many('student.exam', 'exam_student_rel', 'student_id', 'exam_id', 'Exams', compute=_get_exam)
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: