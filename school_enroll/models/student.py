# -*- coding: utf-8 -*-

from openerp import models, api, _, fields

class school_class(models.Model):
    _inherit = 'school.student'
    
    @api.one
    def _get_enroll(self):
        enroll_ids = []
        enroll_line_obj = self.env['student.enroll.line']
        enroll_line_ids = enroll_line_obj.search([('student_id', '=', self.id), ('enroll_id.state', '=', 'enrolled')])
        for line in enroll_line_ids:
            enroll_ids.append(line.enroll_id.id)
        self.enroll_ids = enroll_ids
        
    enroll_ids = fields.Many2many('student.enroll', 'enroll_student_rel', 'student_id', 'enroll_id', 'Enrollment', 
        compute=_get_enroll)
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: