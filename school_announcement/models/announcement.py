# -*- coding: utf-8 -*-

from openerp import models, api, _, fields

import time
    
class school_announcement(models.Model):
    _name = 'school.announcement'
    _description = 'School Announcement'
    _order = 'name desc'
    
    name = fields.Char('Reference')
    title = fields.Char('Title')
    description = fields.Text('Description')
    date_publish = fields.Date('Published Date')
    state = fields.Selection([('draft', 'Draft'), ('published', 'Published')], 'Status', default='draft')
    
    def create(self, cr, uid, vals, context=None):
        vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'school.announcement', context=context)
        return super(school_announcement, self).create(cr, uid, vals, context=context)
    
    @api.multi
    def action_publish(self):
        self.state = 'published'
        self.date_publish = time.strftime('%Y-%m-%d')
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: