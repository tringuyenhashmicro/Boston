# -*- coding: utf-8 -*-

from openerp import models, api, _, fields
from openerp.exceptions import Warning

import time

class student_deposit(models.Model):
    _name = 'student.deposit'
    _description = 'Student Deposit'
    _order = 'name desc'

    @api.onchange('student_id')
    def _onchange_student(self):
        if self.student_id:
            self.parent_id = self.student_id.parent_id.id
        else:
            self.parent_id = False
                
    @api.multi
    def _get_payment_method(self):
        pay_method_ids = self.env['student.payment.method'].search([], limit=1)
        return pay_method_ids and pay_method_ids[0].id or False
    
    name = fields.Char('Reference', default='/')
    student_id = fields.Many2one('school.student', 'Deposit From')
    class_id = fields.Many2one('school.class', 'Class')
    state = fields.Selection([('draft', 'Draft'), ('posted', 'Posted'), ('converted', 'Converted to Revenue'), ('cancel', 'Cancelled')], 'Status', default='draft')
    date = fields.Date('Date Received', default=lambda *a: time.strftime("%Y-%m-%d"))
    amount = fields.Float('Paid Amount')
    parent_id = fields.Many2one('school.student', 'Parent', domain=[('is_parent', '=', True)])
    payment_method_id = fields.Many2one('student.payment.method', 'Payment Method', default=_get_payment_method)
    deposit_lines = fields.One2many('student.deposit.line', 'deposit_id', 'Deposit Lines')
    
    @api.multi
    def action_validate(self):
        if self.amount <= 0:
            raise Warning("Enter Paid Amount !")
        total_amount = 0.0
        for line in self.deposit_lines:
            total_amount += line.amount
        if total_amount != self.amount:
             raise Warning("Line Total should match with Paid Amount !")
        if self.name == '/':
            self.name = self.pool.get('ir.sequence').get(self._cr, self._uid, 'stud.deposit')
        self.state = 'posted'
        
    @api.multi
    def action_cancel(self):
        self.write({'state': 'cancel', 'name': '/'})
        
    @api.multi
    def action_draft(self):
        self.state = 'draft'
        
    @api.multi
    def action_convert_revenue(self):
        self.state = 'converted'
    
    def copy(self, cr, uid, id, default=None, context=None):
        default = dict(context or {})
        default.update({'name': '/', 'state': 'draft'})
        return super(student_deposit, self).copy(cr, uid, id, default, context=context)
        
class student_deposit_line(models.Model):
    _name = 'student.deposit.line'
    _description = 'Student Deposit Line'    
    
    
    @api.one
    def _get_class(self):
        self.class_id = self.deposit_id.class_id.id
    
    @api.one
    def _get_date(self):
        self.date = self.deposit_id.date
        
    student_id = fields.Many2one('school.student', 'Student')
    deposit_id = fields.Many2one('student.deposit', 'Deposit')
    amount = fields.Float('Amount')
    class_id = fields.Many2one('school.class', 'Class', compute=_get_class)
    date = fields.Date('Date Received', compute=_get_date)
    
    @api.onchange('deposit_id')
    def onchange_deposit(self):
        if self.deposit_id:
            student_id = False
            if self.deposit_id.student_id.is_parent:
                student_ids = self.env['school.student'].search([('parent_id', '=', self.deposit_id.student_id.id)])
                student_ids = student_ids and [student.id for student in student_ids] or []
            else:
                self.student_id = self.deposit_id.student_id.id
                student_ids = [self.deposit_id.student_id.id]
            return {
                'domain': {'student_id': [('id', 'in', student_ids)]}
                }
        
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: