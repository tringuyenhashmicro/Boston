# -*- coding: utf-8 -*-

from openerp import models, api, _, fields

class grade_config(models.TransientModel):
    _name = 'grade.config'
    
    @api.multi
    def _get_grades(self):
        grades = []
        grade_ids = self.env['exam.grade'].search([])
        for grade in grade_ids:
            grades.append({'old_name': grade.name, 'name': grade.name, 'mark_from': grade.mark_from, 'mark_to': grade.mark_to})
        return grades
    
    
    @api.multi
    def configure_grades(self):
        grade_obj = self.env['exam.grade']
        grades = [grade.name for grade in self.grade_ids]
        del_grades_ids = grade_obj.search([('name', 'not in', grades)])
        for grade in del_grades_ids:
            grade.unlink()
        for grade in self.grade_ids:
            if grade.old_name:
                grade_ids = grade_obj.search([('name', '=', grade.old_name)])
                grade_ids.write({'name': grade.name, 'mark_from': grade.mark_from, 'mark_to': grade.mark_to})
            else:
                grade_obj.create({'name': grade.name, 'mark_from': grade.mark_from, 'mark_to': grade.mark_to})
        return True
        
    grade_ids = fields.One2many('grade.config.lines', 'config_id', 'Grades', default=_get_grades)
    
class grade_config_lines(models.TransientModel):
    _name = 'grade.config.lines'
    
    config_id = fields.Many2one('grade.config', 'Config')
    name = fields.Char('Grade Name', required=True)
    old_name = fields.Char('Old Grade Name')
    mark_from = fields.Integer('From', required=True)
    mark_to = fields.Integer('To', required=True)
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: