# -*- coding: utf-8 -*-

from openerp import models, api, _, fields
from openerp.exceptions import Warning

class product_update(models.TransientModel):
    _name = 'product.update'
    
    def _get_product(self):
        return self._context['active_id']
    
    quantity = fields.Integer('Quantity')
    product_id = fields.Many2one('school.product', 'Item', default=_get_product)
    type = fields.Selection([('in', 'In'), ('out', 'Out')], 'Type')
    
    @api.one
    def action_update(self):
        transfer_obj = self.env['product.transfer']
        if self.quantity <= 0:
                raise Warning("Enter a positive value")
        if self.type == 'out' and self.quantity > self.product_id.qty_available:
                raise Warning("%s Only %s Qty Available"%(self.product_id.name, self.product_id.qty_available))
        transfer = transfer_obj.create({
            'type': self.type,
            'transfer_ids': [(0, 1, {
                'product_id': self.product_id.id,
                'quantity': self.quantity
                })]
            })
        transfer.action_transfer()
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: