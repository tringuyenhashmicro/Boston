# -*- coding: utf-8 -*-

from openerp import models, api, _, fields
from openerp.exceptions import Warning

import time

class student_invoice(models.Model):
    _name = 'student.invoice'
    _description = 'Student Invoice'
    _order = 'name desc'
    
    @api.multi
    def make_refund(self):
        copy_invoice = False
        for record in self:
            copy_invoice = record.copy(default={'refund_ok': True,
                                                'name'     : '/'})
            for lines in record.invoice_lines:
                lines.copy(default={'invoice_id': copy_invoice.id,})
        return {
            'name': 'Refund Invoice',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'student.invoice',
            'res_id'   : copy_invoice and copy_invoice.id or False,
            'target': 'current',
        }
    
    @api.onchange('student_id')
    def _onchange_student(self):
        if not self.student_id:
            self.parent_id = False
        if self.student_id:
            self.parent_id = self.student_id.parent_id and self.student_id.parent_id.id
                
    @api.one
    @api.depends('invoice_lines.quantity', 'invoice_lines.price_unit', 'invoice_lines.subtotal')
    def _amount_total(self):
        total, balance  = 0.0, 0.0
        for line in self.invoice_lines:
            total += line.quantity * line.price_unit
        balance = total - self.amount_paid
        self.amount_total = total
        self.amount_balance = balance
    
    @api.one
    def _paid_sessions(self):
        qty_paid = self.amount_total and (self.amount_paid/self.amount_total) * self.session_qty or 0
        self.session_qty_paid = qty_paid
    
    name = fields.Char('Invoice Number', default='/')
    student_id = fields.Many2one('school.student', 'Bill To')
    invoice_lines = fields.One2many('student.invoice.line', 'invoice_id', 'Invoice Lines')
    state = fields.Selection([('draft', 'Draft'), ('open', 'Open'), ('paid', 'Paid'), ('cancel', 'Cancelled')], 'Status', default='draft')
    date = fields.Date('Invoice Date', default=lambda *a: time.strftime("%Y-%m-%d"))
    amount_total = fields.Float('Total', compute='_amount_total', store=True)
    amount_paid = fields.Float('Paid')
    amount_balance = fields.Float('Balance', compute='_amount_total')
    class_id = fields.Many2one('school.class', 'Class')
    session_qty = fields.Integer('Number of Sessions')
    session_qty_paid = fields.Integer('Paid Sessions', compute=_paid_sessions)
    parent_id = fields.Many2one('school.student', 'Parent', domain=[('is_parent', '=', True)])
    enroll_id = fields.Many2one('student.enroll', 'Enroll')
    refund_ok = fields.Boolean('Refund Invoice')
    
    @api.multi
    def action_validate(self):
        self.state = 'open'
        if self.name == '/':
            self.name = self.pool.get('ir.sequence').get(self._cr, self._uid, 'stud.invoice') 
        
    @api.multi
    def action_cancel(self):
        if self.amount_paid > 0.0:
            raise Warning("Cancel the payment to cancel the Invoice !")
        self.write({'state': 'cancel'})
        
    @api.multi
    def action_draft(self):
        self.state = 'draft'
        
class student_invoice_line(models.Model):
    _name = 'student.invoice.line'
    _description = 'Student Invoice Line'
    
    @api.one
    @api.depends('quantity', 'price_unit')
    def _subtotal(self):
        self.subtotal = self.quantity * self.price_unit
        
    invoice_id = fields.Many2one('student.invoice', 'Invoice')
    student_id = fields.Many2one('school.student', 'Student')
    name = fields.Char('Description')
    price_unit = fields.Float('Unit Price')
    quantity = fields.Integer('Quantity')
    subtotal = fields.Float('Subtotal', compute='_subtotal')
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: