# -*- coding: utf-8 -*-

from openerp import models, api, _, fields

class book_update(models.TransientModel):
    _name = 'book.update'
    
    def _get_book(self):
        return self._context['active_id']
    
    quantity = fields.Integer('Quantity')
    book_id = fields.Many2one('school.book', 'Book', default=_get_book)
    
    @api.one
    def action_update(self):
        transfer_obj = self.env['book.transfer']
        holder_obj = self.env['book.holder']
        dest_holder_id = holder_obj.search([('type', '=', 'school')])[0].id
        transfer = transfer_obj.create({
            'dest_holder_id': dest_holder_id,
            'type': 'school',
            'transfer_ids': [(0, 1, {
                'book_id': self.book_id.id,
                'quantity': self.quantity
                })]
            })
        transfer.action_transfer()
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: