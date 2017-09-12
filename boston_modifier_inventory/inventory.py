from openerp import models, fields, api, _
    
class SchoolProductCate(models.Model):
    _name = 'school.product.cate'
    name = fields.Char('Name', size=256)
    
class SchoolProduct(models.Model):
    _inherit = 'school.product'
    cate_id = fields.Many2one('school.product.cate', string='Category')
    course_id = fields.Many2one('school.school', string='Course')
    
class ProductTransfer(models.Model):
    _inherit = 'product.transfer'
    remark = fields.Text(string='Remark')
    
class ProductUpdate(models.TransientModel):
    _inherit = 'product.update'
        
    remark = fields.Text(string='Remark')
    
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
                'quantity'  : self.quantity,
                })],
            'remark'    : self.remark,
            })
        transfer.action_transfer()
        return 1