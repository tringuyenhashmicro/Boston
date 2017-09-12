# -*- coding: utf-8 -*-

from openerp import models, api, _, fields

class student_enroll(models.Model):
    _inherit = 'student.enroll'
    
    invoice_ids = fields.One2many('student.invoice', 'enroll_id', 'Invoices')
    
    @api.onchange('class_id')
    def _onchange_class(self):
        self.credit = 0
        if self.class_id:
            for line in self.line_ids:
                credit_ids = self.env['student.credit'].search([
                    ('class_id', '=', self.class_id.id),
                    ('student_id', '=', line.student_id.id)
                    ])
                if credit_ids:
                    line.credit = credit_ids[0].credit
                
                
    @api.multi
    def action_batch_enroll(self):
        enroll = super(student_enroll, self).action_batch_enroll()
        for line in self.line_ids:
            credit_ids = self.env['student.credit'].search([
                ('class_id', '=', self.class_id.id),
                ('student_id', '=', line.student_id.id)
                ])
            credit = 0
            if credit_ids:
                credit = credit_ids[0].credit
            self.env['student.enroll.line'].create({
                'student_id': line.student_id.id,
                'enroll_id': enroll.id,
                'credit': credit
                })
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(
            self._cr, self._uid, 'school_enroll', 'view_student_enroll_form')
        return {
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'student.enroll',
            'res_id': enroll.id,
            'type': 'ir.actions.act_window',
            }

    @api.multi
    def action_enroll(self):
        super(student_enroll, self).action_enroll()
        inv_obj = self.env['student.invoice']
        std_class = self.class_id
        fees = []
        if len(std_class.enroll_fee_ids) == 1:
            fees += [std_class.enroll_fee_ids]
        else:
            fees += std_class.enroll_fee_ids
        if len(std_class.enroll_rec_ids) == 1:
            fees += [std_class.enroll_rec_ids]
        else:
            fees += std_class.enroll_rec_ids
        # fees = [std_class.enroll_fee_ids, std_class.enroll_rec_ids]
        config_obj = self.env['ir.config_parameter']
        config_vals = {'first_signup': 'First Signup', 'recurring_fees': 'Recurring Fees'}
        lines = []
        for fee_config in config_vals.keys():
            config_ids = config_obj.search([('key', '=', fee_config)])
            if config_ids:
                lines.append((0, 1, {
                    'name': config_vals[fee_config],
                    'quantity': 1,
                    'price_unit': config_ids[0].value,
                    }))
        for fee in fees:
            for line in fee:
                if fee.amount > 0:
                    lines.append((0, 1, {
                        'name': line.fee_id.name,
                        'quantity': 1,
                        'price_unit': line.amount,
                        }))
        if lines:
            inv_parent = {}
            for line in self.line_ids:
                student_id = line.student_id.id
                parent_id = line.student_id.parent_id and line.student_id.parent_id.id or False
                for inv_line in lines:
                    inv_line[2].update({'student_id': student_id})
                inv_vals = {
                        'student_id': student_id,
                        'class_id': std_class.id,
                        'parent_id': parent_id,
                        'session_qty': len(std_class.session_ids),
                        'invoice_lines': lines,
                        'enroll_id': self.id,
                        }
                if line.student_id.bill_parent and line.student_id.parent_id:
                    inv_vals.update({'student_id': parent_id})
                    if parent_id in inv_parent.keys():
                        invoice = inv_parent[parent_id]
                        invoice.write({'invoice_lines': lines})
                    else:
                        invoice = inv_obj.create(inv_vals)
                        inv_parent.update({parent_id: invoice})
                    line.invoice_id = invoice.id
                else:
                    invoice = inv_obj.create(inv_vals)
                    line.invoice_id = invoice.id

class student_enroll_line(models.Model):
    _inherit = 'student.enroll.line'
    
    @api.one
    @api.depends('enroll_id.class_id', 'student_id')
    def _get_credits(self):
        credit_ids = self.env['student.credit'].search([
            ('class_id', '=', self.enroll_id.class_id.id),
            ('student_id', '=', self.student_id.id)
            ])
        if credit_ids:
            self.credit = credit_ids[0].credit
        else:
            self.credit = 0 
        
    credit = fields.Integer('Credits Remaining', compute=_get_credits)
    invoice_id = fields.Many2one('student.invoice', 'Invoice')
    invoice_refund_id = fields.Many2one('student.invoice', 'Refund Invoice')
    
    @api.multi
    def action_refund(self):
        inv_obj = self.env['student.invoice']
        lines = [(0, 1, {
            'name': 'Refund',
            'quantity': 1,
            'student_id': self.student_id.id
            })]
        if self.student_id.bill_parent and self.student_id.parent_id:
            student_id = self.student_id.parent_id.id
        inv_vals = {
            'student_id': student_id,
            'class_id': self.enroll_id.class_id.id,
            'parent_id': self.student_id.parent_id.id,
            'session_qty': self.credit,
            'invoice_lines': lines,
            'enroll_id': self.enroll_id.id,
            'refund_ok': True
            }
        invoice = inv_obj.create(inv_vals)
        self.invoice_refund_id = invoice.id
        self.refund_ok = True
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(
            self._cr, self._uid, 'school_billing', 'view_student_invoice_form')
        return {
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'student.invoice',
            'res_id': invoice.id,
            'type': 'ir.actions.act_window',
            }
    
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: