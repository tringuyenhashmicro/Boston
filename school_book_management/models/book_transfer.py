# -*- coding: utf-8 -*-

from openerp import models, api, _, fields
from openerp.exceptions import Warning

import time

class book_holder(models.Model):
    _name = 'book.holder'
    _inherit = ['mail.thread']
    _description = 'Books Holder'
    
    @api.one
    def _qty_available(self):
        qty_in, qty_out = 0, 0
        transfer_obj = self.env['book.transfer.line']
        in_list = transfer_obj.search([('state', '=', 'done'), ('dest_holder_id', '=', self.id)])
        out_list = transfer_obj.search([('state', '=', 'done'), ('holder_id', '=', self.id)])
        for transfer in in_list:
            qty_in += transfer.quantity
        for transfer in out_list:
            qty_out += transfer.quantity
        self.quantity = qty_in - qty_out
     
    @api.multi
    def get_ttype(self):
#         for record in self.browse(self.ids):
        if self.env.context.has_key('ttype'):
            return self.env.context['ttype']
        return ''
                
        
    name = fields.Char('Name', required=True)
    type = fields.Selection([('school', 'School'), 
                             ('teacher', 'Teacher'), 
                             ('student', 'Student'), 
                             ('inv', 'Inventory')], 'Type', default=get_ttype)
    quantity = fields.Integer('Total Books', compute=_qty_available)
    
    def qty_available(self, book_id):
        qty_in, qty_out = 0, 0
        transfer_obj = self.env['book.transfer.line']
        in_list = transfer_obj.search([('state', '=', 'done'), ('dest_holder_id', '=', self.id), ('book_id', '=', book_id)])
        out_list = transfer_obj.search([('state', '=', 'done'), ('holder_id', '=', self.id), ('book_id', '=', book_id)])
        for transfer in in_list:
            qty_in += transfer.quantity
        for transfer in out_list:
            qty_out += transfer.quantity
        qty = qty_in - qty_out
        return qty
        
class book_transfer(models.Model):
    _name = 'book.transfer'
    _inherit = ['mail.thread']
    _description = 'Books Transfer'
    _order = 'name desc'
    
    
    def _get_holder(self):
        if 'school' in self._context:
            return self.env['book.holder'].search([('type', '=', 'school')])[0].id
        else:
            return False
        
    name = fields.Char('Reference', default='/')
    date = fields.Date('Date of Transfer', default=time.strftime('%Y-%m-%d'))
    state = fields.Selection([('draft', 'Draft'), ('done', 'Transferred')], 'Status', default='draft')
    transfer_ids = fields.One2many('book.transfer.line', 'transfer_id', 'Transfer Lines')
    holder_id = fields.Many2one('book.holder', 'From', default=_get_holder)
    dest_holder_id = fields.Many2one('book.holder', 'To')
    type = fields.Selection([('school', 'School'), ('teacher', 'Teacher'), ('student', 'Student')])
    
    def create(self, cr, uid, vals, context=None):
        vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'book.transfer', context=context)
        return super(book_transfer, self).create(cr, uid, vals, context=context)
    
    @api.multi
    def action_transfer(self):
        self.state = 'done'
        
    @api.multi
    def action_transfer_teacher(self):
        for line in self.transfer_ids:
            if line.book_id.qty_school < line.quantity:
                raise Warning("%s Only %s Qty Available"%(line.book_id.name, line.book_id.qty_school))
        self.state = 'done'
    
    @api.multi
    def action_transfer_student(self):
        for line in self.transfer_ids:
            qty_available = self.holder_id.qty_available(line.book_id.id)
            if qty_available < line.quantity:
                raise Warning("%s Only %s Qty Available"%(line.book_id.name, qty_available))
        self.state = 'done'
        
class book_transfer_line(models.Model):
    _name = 'book.transfer.line'
    _inherit = ['mail.thread']
    _description = 'Books Transfer Lines'
    _order = 'id desc'
    
    @api.one
    @api.depends('transfer_id', 'transfer_id.state', 'transfer_id.holder_id', 'transfer_id.dest_holder_id', 'transfer_id.date')
    def _get_details(self):
        self.state = self.transfer_id.state
        self.holder_id = self.transfer_id.holder_id.id
        self.dest_holder_id = self.transfer_id.dest_holder_id.id
        self.date = self.transfer_id.date
    
    @api.one
    def _get_type(self):
        self.type = self.transfer_id.dest_holder_id.type
            
    transfer_id = fields.Many2one('book.transfer', 'Book Transfer', ondelete='cascade')
    book_id = fields.Many2one('school.book', 'Book')
    quantity = fields.Integer('Quantity')
    holder_id = fields.Many2one('book.holder', 'From', compute=_get_details, store=True)
    dest_holder_id = fields.Many2one('book.holder', 'To', compute=_get_details, store=True)
    date = fields.Date('Date of Transfer', compute=_get_details, store=True)
    state = fields.Selection([('draft', 'Draft'), ('done', 'Transferred')], 'Status', compute=_get_details, store=True)
    type = fields.Char('Type', compute=_get_type)
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: