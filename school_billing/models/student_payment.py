# -*- coding: utf-8 -*-

from openerp import models, api, _, fields
from openerp.exceptions import Warning

import time

    
class student_payment_method(models.Model):
    _name = 'student.payment.method'
    _description = 'Student Payment Method'
    
    name = fields.Char('Name', required=True)
    
class student_payment(models.Model):
    _name = 'student.payment'
    _description = 'Student Payment'
    _order = 'name desc'
    
    @api.onchange('student_id')
    def _onchange_student(self):
        if not self.student_id:
            raise Warning('Call this function!!!!')
            self.payment_lines = False
        if self.student_id:
            student_id = self.student_id.id
            self.parent_id = self.student_id.parent_id.id
            self.payment_lines = False
            payment_list = []
            inv_obj = self.env['student.invoice']
            if 'inv_id' in self._context:
                invoice = self.env['student.invoice'].browse(self._context['inv_id'])
                if invoice.refund_ok: self.refund_ok = True
                inv_ids = [invoice]
            else:
                domain = [('student_id', '=', student_id), ('state', '=', 'open')]
                if 'default_refund_ok' in self._context:
                    domain.append(('refund_ok', '=', True))
                inv_ids = inv_obj.search(domain)
            # raise Warning(str(inv_ids))
            for inv in inv_ids:
                rs = {
                    'invoice_amount': inv.amount_total,
                    'date': inv.date,
                    'balance': inv.amount_balance,
                    'inv_id': inv.id,
                    'class_id': inv.class_id.id,
                    'amount': inv.amount_balance,
                    'session_qty': (inv.amount_balance/inv.amount_total) * inv.session_qty
                    }
                payment_list.append((0, 1, rs))
            if payment_list:
                self.payment_lines = payment_list
        
    @api.multi
    def action_validate(self):
        if self.amount <= 0:
            raise Warning("Enter Paid Amount !")
        if 'inv_id' in self._context:
            inv_id = self._context['inv_id']
            invoice = self.env['student.invoice'].browse(inv_id)
            if self.amount > invoice.amount_balance:
                raise Warning("Amount exceeds Balance !")
        else:
            total_amount = 0.0
            for line in self.payment_lines:
                total_amount += line.amount
                if line.amount > line.balance:
                    raise Warning("Amount exceeds Balance !")
            if total_amount != self.amount:
                 raise Warning("Line Total should match with Paid Amount !")
        class_list = []
        credit_obj = self.env['student.credit']
        for line in self.payment_lines:
            student_ids = list(set([inv_line.student_id.id for inv_line in line.inv_id.invoice_lines]))
            for student_id in student_ids:
                credit_ids = credit_obj.search([
                    ('class_id', '=', line.class_id.id),
                    ('student_id', '=', student_id),
                    ])
                if not credit_ids:
                    credit_obj.create({'class_id': line.class_id.id, 'student_id': student_id})
            if 'inv_id' in self._context:
                line.amount = self.amount
            paid_amount = line.inv_id.amount_paid + line.amount
            line.inv_id.amount_paid = paid_amount
            if paid_amount == line.inv_id.amount_total:
                line.inv_id.state = 'paid'
                
                #For Updating Credit in Enrollment
#                 if self.refund_ok:
#                     enroll_line_obj = self.env['student.enroll.line']
#                     enroll_line_ids = enroll_line_obj.search([
#                         ('student_id', '=', self.student_id.id), ('enroll_id', '=', line.inv_id.enroll_id.id)
#                         ])
#                     for enroll_line in enroll_line_ids:
#                         enroll_line.credit = 0
#                         enroll_line.credit_org = 0
                
                #For Updating Credit in Enrollment
                
        if self.name == '/':
            self.name = self.pool.get('ir.sequence').get(self._cr, self._uid, 'stud.payment')
        self.state = 'posted'
        
    @api.multi
    def action_cancel(self):
        self.write({'state': 'cancel', 'name': '/'})
        for line in self.payment_lines:
            paid_amount = line.inv_id.amount_paid - line.amount
            line.inv_id.amount_paid = paid_amount
            line.inv_id.state = 'open'
                
    @api.multi
    def action_draft(self):
        self.state = 'draft'
    
    @api.multi
    def _get_payment_method(self):
        pay_method_ids = self.env['student.payment.method'].search([], limit=1)
        return pay_method_ids and pay_method_ids[0].id or False
        
    name = fields.Char('Reference', default='/')
    student_id = fields.Many2one('school.student', 'Payment From')
    payment_lines = fields.One2many('student.payment.line', 'payment_id', 'Payment Lines')
    state = fields.Selection([('draft', 'Draft'), ('posted', 'Posted'), ('cancel', 'Cancelled')], 'Status', default='draft')
    date = fields.Date('Date', default=lambda *a: time.strftime("%Y-%m-%d"))
    amount = fields.Float('Paid Amount')
    parent_id = fields.Many2one('school.student', 'Parent', domain=[('is_parent', '=', True)])
    refund_ok = fields.Boolean('Refund Payment')
    payment_method_id = fields.Many2one('student.payment.method', 'Payment Method', default=_get_payment_method)
    
class student_payment_line(models.Model):
    _name = 'student.payment.line'
    _description = 'Student Payment Line'
    
    @api.one
    @api.depends('session_qty', 'price_unit')
    def _subtotal(self):
        self.amount = self.session_qty * self.price_unit
        
    payment_id = fields.Many2one('student.payment', 'Payment')
    date = fields.Date('Invoice Date')
    invoice_amount = fields.Float('Invoice Amount')
    balance = fields.Float('Balance')
    amount = fields.Float('Amount')
    inv_id = fields.Many2one('student.invoice', 'Invoice')
    class_id = fields.Many2one('school.class', 'Class')
    session_qty = fields.Integer('Sessions')
    price_unit = fields.Float('Price Unit')
    
