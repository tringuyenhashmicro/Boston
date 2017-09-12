# -*- coding: utf-8 -*-

from openerp import models, api, _, fields

class school_class(models.Model):
    _inherit = 'school.class'
    
    @api.one
    def _get_enrolled_students(self):
        enroll_obj = self.env['student.enroll']
        enroll_ids = enroll_obj.search([('class_id', '=', self.id), ('state', '=', 'enrolled')])
        student_ids = []
        for enroll in enroll_ids:
            for line in enroll.line_ids:
                student_ids.append(line.student_id.id)
        self.student_ids = list(set(student_ids))
        self.enroll_ids = enroll_ids
    
    student_ids = fields.Many2many('school.student', 'class_stud_rel', 'class_id', 'student_id', 'Students',
        compute='_get_enrolled_students')
    enroll_ids = fields.Many2many('student.enroll', 'class_enroll_rel', 'class_id', 'enroll_id', 'Enrollment',
        compute='_get_enrolled_students')
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: