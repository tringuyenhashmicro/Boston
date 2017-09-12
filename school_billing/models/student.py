# -*- coding: utf-8 -*-

from openerp import models, api, _, fields

class school_student(models.Model):
    _inherit = 'school.student'
    
    @api.one
    def _get_deposit(self):
        deposit_ids, total_deposit = [], 0.0
        deposit_line_obj = self.env['student.deposit.line']
        if self.is_parent:
            deposit_line_ids = deposit_line_obj.search([
                ('student_id', 'child_of', self.id), ('deposit_id.state', '=', 'posted')], order='id desc')
        else:
            deposit_line_ids = deposit_line_obj.search([
                ('student_id', '=', self.id), ('deposit_id.state', '=', 'posted')], order='id desc')
        for line in deposit_line_ids:
            deposit_ids.append(line.id)
            total_deposit += line.amount
        self.deposit_ids = deposit_ids
        self.total_deposit = total_deposit
        
    credit_ids = fields.One2many('student.credit', 'student_id', 'Credits')
    deposit_ids = fields.Many2many('student.deposit.line', 'deposit_student_rel', 'student_id', 'deposit_id', 'Deposit', 
        compute=_get_deposit)
    total_deposit = fields.Float('Total Deposit', compute=_get_deposit)

class student_credit(models.Model):
    _name = 'student.credit'
    _description = 'Student Credits'
    
    @api.one
    @api.depends('class_id', 'student_id')
    def _get_credits(self):
        credit = 0
        inv_ids1 = self.env['student.invoice'].search([
            ('student_id', '=', self.student_id.id),
            ('class_id', '=', self.class_id.id),
            ('state', 'in', ('open', 'paid'))
            ])
        inv_line_obj = self.env['student.invoice.line']
        inv_line_ids = inv_line_obj.search([
            ('student_id', '=', self.student_id.id),
            ('invoice_id.class_id', '=', self.class_id.id),
            ('invoice_id.state', 'in', ('open', 'paid'))
            ])
        inv_ids2 = list(set([inv_line.invoice_id for inv_line in inv_line_ids]))
        if isinstance(inv_ids1, list) and isinstance(inv_ids2, list): invoice_ids = inv_ids1 + inv_ids2
        elif isinstance(inv_ids1, list): invoice_ids = inv_ids1
        elif isinstance(inv_ids2, list): invoice_ids = inv_ids2
        for invoice in invoice_ids:
            sign = 1
            if invoice.refund_ok:
                sign = -1
            credit += invoice.session_qty_paid * sign
        att_line_ids = self.env['student.attendance.line'].search([
            ('student_id', '=', self.student_id.id),
            ('attendance_id.class_id', '=', self.class_id.id),
            ('attendance_id.state', '=', 'posted'),
            ('present_ok', '=', True)
            ])
        credit -= len(att_line_ids)
        self.credit = credit
        
    student_id = fields.Many2one('school.student', 'Student')
    class_id = fields.Many2one('school.class', 'Class')
    credit = fields.Integer('Credits Remaining', compute=_get_credits)  

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: