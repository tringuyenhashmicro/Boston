# -*- coding: utf-8 -*-

from openerp import models, api, _, fields

class school_school(models.Model):
    _name = 'school.school'
    _description = 'Subject'
    
    name = fields.Char('Subject Name', required=True)
    description = fields.Char('Description')
    level = fields.Char('Level')
    objective = fields.Text('Objectives')
    class_ids = fields.One2many('school.class', 'subject_id', 'Classes')

class school_subject(models.Model):
    _name = 'school.subject'
    _description = 'Subject'
    
    name = fields.Char('Subject Name', required=True)
    description = fields.Char('Description')
    level = fields.Char('Level')
    objective = fields.Text('Objectives')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: