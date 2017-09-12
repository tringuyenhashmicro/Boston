# -*- coding: utf-8 -*-

from openerp import models, api, _, fields

class student_configuration(models.TransientModel):
    _name = 'student.config.settings'
    _inherit = 'res.config.settings'
    
    @api.multi
    def _get_default_credithours(self):
        credit_ids = self.env['ir.config_parameter'].search([('key', '=', 'credit_hours')])
        return credit_ids and credit_ids[0].value or 0
    
    @api.multi
    def _get_default_first_signup(self):
        signup_ids = self.env['ir.config_parameter'].search([('key', '=', 'first_signup')])
        return signup_ids and signup_ids[0].value or 0
    
    @api.multi
    def _get_default_recurring_fees(self):
        recurring_ids = self.env['ir.config_parameter'].search([('key', '=', 'recurring_fees')])
        return recurring_ids and recurring_ids[0].value or 0
        
    credit_hours = fields.Float('Credit Hours', default=_get_default_credithours)
    first_signup = fields.Float('First Signup', default=_get_default_first_signup)
    recurring_fees = fields.Float('Recurring Fees', default=_get_default_recurring_fees)
    
    @api.multi
    def set_default_settings(self):
        config_obj = self.env['ir.config_parameter']
        config_vals = {'credit_hours': self.credit_hours, 'first_signup': self.first_signup, 'recurring_fees': self.recurring_fees}
        for field in config_vals.keys():
            config_ids = config_obj.search([('key', '=', field)])
            if config_ids: config_ids[0].write({'value': config_vals[field]})
            else: config_obj.create({'key': field, 'value': config_vals[field]})
        
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: