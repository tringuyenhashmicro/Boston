# -*- coding: utf-8 -*-

from openerp import models, api, _, fields
from openerp.exceptions import Warning

import time

class product_transfer(models.Model):
    _name = 'product.transfer'
    _inherit = ['mail.thread']
    _description = 'Product Transfer'
    _order = 'name desc'
    
    name = fields.Char('Reference')
    date = fields.Date('Date', default=time.strftime('%Y-%m-%d'))
    transfer_ids = fields.One2many('product.transfer.line', 'transfer_id', 'Transfer Lines')
    type = fields.Selection([('in', 'In'), ('out', 'Out')], 'Type')
    state = fields.Selection([('draft', 'Draft'), ('done', 'Transferred')], 'Status', default='draft')
    
    def create(self, cr, uid, vals, context=None):
        if vals['type'] == 'in':
            vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'product.transfer.in', context=context)
        elif vals['type'] == 'out':
            vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'product.transfer.out', context=context)
        return super(product_transfer, self).create(cr, uid, vals, context=context)
    
    
    @api.multi
    def action_transfer(self):
        for line in self.transfer_ids:
            if self.type == 'out' and line.quantity > line.product_id.qty_available:
                raise Warning("%s Only %s Qty Available"%(line.product_id.name, line.product_id.qty_available))
        self.state = 'done'
    
class product_transfer_line(models.Model):
    _name = 'product.transfer.line'
    _inherit = ['mail.thread']
    _description = 'Product Transfer Line'
    _order = 'id desc'
    
    @api.one
    @api.depends('transfer_id', 'transfer_id.state', 'transfer_id.type', 'transfer_id.date')
    def _get_details(self):
        self.state, self.type, self.date = self.transfer_id.state, self.transfer_id.type, self.transfer_id.date
    
    transfer_id = fields.Many2one('product.transfer', 'Book Transfer', ondelete='cascade')
    product_id = fields.Many2one('school.product', 'Product', required=True)
    quantity = fields.Integer('Quantity', required=True)
    state = fields.Selection([('draft', 'Draft'), ('done', 'Transferred')], 'Status', compute=_get_details, store=True)
    type = fields.Selection([('in', 'In'), ('out', 'Out')], 'Type', compute=_get_details, store=True)
    date = fields.Date('Date', compute=_get_details, store=True)
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: