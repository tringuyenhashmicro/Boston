# -*- coding: utf-8 -*-

from openerp import models, api, _, fields

class school_class(models.Model):
    _name = 'school.class'
    _description = 'Class'
    
    name = fields.Char('Class Name', required=True)
    subject_id = fields.Many2one('school.school', 'Subject', required=True)
    location = fields.Char('Location')
    teacher_id = fields.Many2one('hr.employee', 'Teacher')
    session_ids = fields.One2many('school.session', 'class_id', 'Sessions')
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: