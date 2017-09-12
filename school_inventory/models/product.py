# -*- coding: utf-8 -*-

from openerp import models, api, _, fields
from openerp.exceptions import Warning

import time

class school_product(models.Model):
    _name = 'school.product'
    _inherit = ['mail.thread']
    _description = 'Product'
    
    @api.one
    def _get_qty(self):
        qty_in, qty_out = 0, 0
        transfer_obj = self.env['product.transfer.line']
        in_list = transfer_obj.search([('state', '=', 'done'), ('product_id', '=', self.id), ('type', '=', 'in')])
        out_list = transfer_obj.search([('state', '=', 'done'), ('product_id', '=', self.id), ('type', '=', 'out')])
        for transfer in in_list:
            qty_in += transfer.quantity
        for transfer in out_list:
            qty_out += transfer.quantity
        self.qty_available = qty_in - qty_out
        
    name = fields.Char('Product Name', required=True)
    code = fields.Char('Product Code')
    qty_available = fields.Integer('Available Qty', compute=_get_qty)
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: