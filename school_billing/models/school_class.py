# -*- coding: utf-8 -*-

from openerp import models, api, _, fields

class school_class(models.Model):
    _inherit = 'school.class'
    
    @api.one
    @api.depends('enroll_fee_ids', 'enroll_fee_ids.amount')
    def _enroll_fee_total(self):
        total = 0.0
        for fee in self.enroll_fee_ids:
           total += fee.amount
        self.enroll_fee_total = total
        
    @api.one
    @api.depends('enroll_rec_ids', 'enroll_rec_ids.amount')
    def _enroll_rec_total(self):
        total = 0.0
        for fee in self.enroll_rec_ids:
           total += fee.amount
        self.enroll_rec_total = total
    
    @api.one
    def _get_deposit(self):
        deposit_ids, total_deposit = [], 0.0
        deposit_line_ids = self.env['student.deposit.line'].search([
            ('deposit_id.class_id', '=', self.id), ('deposit_id.state', '=', 'posted')], order='id desc')
        for line in deposit_line_ids:
            deposit_ids.append(line.id)
            total_deposit += line.amount
        self.deposit_ids = deposit_ids
        self.total_deposit = total_deposit

    enroll_fee_ids = fields.One2many('fee.enroll', 'class_id', 'First Enrollment')
    enroll_rec_ids = fields.One2many('fee.enroll.recurring', 'class_id', 'Recurring Enrollment')
    enroll_fee_total = fields.Float('Total Fee', compute=_enroll_fee_total)
    enroll_rec_total = fields.Float('Total Fee', compute=_enroll_rec_total)
    deposit_ids = fields.Many2many('student.deposit.line', 'deposit_class_rel', 'class_id', 'deposit_id', 'Deposit',  
        compute=_get_deposit)
    total_deposit = fields.Float('Total Deposit', compute=_get_deposit)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: