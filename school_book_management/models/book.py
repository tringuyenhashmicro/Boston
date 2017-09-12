# -*- coding: utf-8 -*-

from openerp import models, api, _, fields

class school_book(models.Model):
    _name = 'school.book'
    _inherit = ['mail.thread']
    _description = 'Books'
    
    @api.one
    def _qty_school(self):
        qty_in, qty_out = 0, 0
        transfer_obj = self.env['book.transfer.line']
        in_list = transfer_obj.search([('state', '=', 'done'), ('book_id', '=', self.id), ('dest_holder_id.type', '=', 'school')])
        out_list = transfer_obj.search([('state', '=', 'done'), ('book_id', '=', self.id), ('holder_id.type', '=', 'school')])
        for transfer in in_list:
            qty_in += transfer.quantity
        for transfer in out_list:
            qty_out += transfer.quantity
        self.qty_school = qty_in - qty_out
    
    @api.one
    def _qty_teacher(self):
        qty_in, qty_out = 0, 0
        transfer_obj = self.env['book.transfer.line']
        in_list = transfer_obj.search([('state', '=', 'done'), ('book_id', '=', self.id), ('dest_holder_id.type', '=', 'teacher')])
        out_list = transfer_obj.search([('state', '=', 'done'), ('book_id', '=', self.id), ('holder_id.type', '=', 'teacher')])
        for transfer in in_list:
            qty_in += transfer.quantity
        for transfer in out_list:
            qty_out += transfer.quantity
        self.qty_teacher = qty_in - qty_out
        
    @api.one
    def _qty_student(self):
        qty_in, qty_out = 0, 0
        transfer_obj = self.env['book.transfer.line']
        in_list = transfer_obj.search([('state', '=', 'done'), ('book_id', '=', self.id), ('dest_holder_id.type', '=', 'student')])
        out_list = transfer_obj.search([('state', '=', 'done'), ('book_id', '=', self.id), ('holder_id.type', '=', 'student')])
        for transfer in in_list:
            qty_in += transfer.quantity
        for transfer in out_list:
            qty_out += transfer.quantity
        self.qty_student = qty_in - qty_out
    
    @api.one
    def _qty_qty(self):
        qty_in, qty_out = 0, 0
        transfer_obj = self.env['book.transfer.line']
        if 'holder_id' in self._context:
            holder_id = self._context['holder_id']
            in_list = transfer_obj.search([('state', '=', 'done'), ('book_id', '=', self.id), ('dest_holder_id', '=', holder_id)])
            out_list = transfer_obj.search([('state', '=', 'done'), ('book_id', '=', self.id), ('holder_id', '=', holder_id)])
            for transfer in in_list:
                qty_in += transfer.quantity
            for transfer in out_list:
                qty_out += transfer.quantity
        self.quantity = qty_in - qty_out
                
    name = fields.Char('Name', required=True)
    qty_school = fields.Integer('Books in Warehouse', compute=_qty_school)
    qty_teacher = fields.Integer('Books with Teachers', compute=_qty_teacher)
    qty_student = fields.Integer('Books with Students', compute=_qty_student)
    quantity = fields.Integer('Quantity', compute=_qty_qty)
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: