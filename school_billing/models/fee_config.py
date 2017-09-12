# -*- coding: utf-8 -*-

from openerp import models, api, _, fields

class fees_category(models.Model):
    _name = 'fees.category'
    _description = 'Fees Category'
    
    name = fields.Char('Category Name', required=True)
    
class fee_config(models.Model):
    _name = 'fee.config'
    _description = 'Fees Configuration'
    
    name = fields.Char('Description')
    amount = fields.Float('Price')
    category_id = fields.Many2one('fees.category', 'Category')
    
class fee_signup(models.Model):
    _name = 'fee.signup'
    _description = 'Sign Up Fee'
    
    @api.onchange('fee_id')
    def _onchange_fee(self):
        if self.fee_id:
            self.amount = self.fee_id.amount
            
    class_id = fields.Many2one('school.class', 'Class')
    fee_id = fields.Many2one('fee.config', 'Description')
    amount = fields.Float('Price')
    category_id = fields.Many2one('fees.category', 'Category')
    
class fee_recurring(models.Model):
    _name = 'fee.recurring'
    _description = 'Recurring Fee'
    
    @api.onchange('fee_id')
    def _onchange_fee(self):
        if self.fee_id:
            self.amount = self.fee_id.amount
    
    class_id = fields.Many2one('school.class', 'Class')
    fee_id = fields.Many2one('fee.config', 'Description')
    amount = fields.Float('Price')
    category_id = fields.Many2one('fees.category', 'Category')

class fee_enroll(models.Model):
    _name = 'fee.enroll'
    _description = 'Enroll Fee'
    
    @api.onchange('fee_id')
    def _onchange_fee(self):
        if self.fee_id:
            self.amount = self.fee_id.amount
    
    class_id = fields.Many2one('school.class', 'Class')
    fee_id = fields.Many2one('fee.config', 'Description')
    amount = fields.Float('Price')
    category_id = fields.Many2one('fees.category', 'Category')

class fee_enroll_recurring(models.Model):
    _name = 'fee.enroll.recurring'
    _description = 'Recurring Enroll Fee'
    
    @api.onchange('fee_id')
    def _onchange_fee(self):
        if self.fee_id:
            self.amount = self.fee_id.amount
    
    class_id = fields.Many2one('school.class', 'Class')
    fee_id = fields.Many2one('fee.config', 'Description')
    amount = fields.Float('Price')
    category_id = fields.Many2one('fees.category', 'Category')
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: