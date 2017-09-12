# -*- coding: utf-8 -*-

from openerp import SUPERUSER_ID, models, api, _, fields

class school_teacher(models.Model):
    _name = 'school.teacher'
    _description = 'Teacher'
    
    name = fields.Char('Teacher Name', required=True)
    email = fields.Char('Email')
    user_id = fields.Many2one('res.users', 'Related User')
    
    def write(self, cr, uid, ids, vals, context=None):
        res = super(school_teacher, self).write(cr, uid, ids, vals, context=context)
        for teacher in self.browse(cr, uid, ids):
            if teacher.user_id:
                teacher.user_id.write({'name': teacher.name, 'email': teacher.email})
            else:
                user_id = self.pool.get('res.users').create(cr, uid, {
                    'name': teacher.name,
                    'login': teacher.email
                    }) 
                teacher.write({'user_id': user_id})
        return res
    
    def create(self, cr, uid, vals, context=None):
        teacher_id = super(school_teacher, self).create(cr, uid, vals, context=context)
        teacher = self.browse(cr, uid, teacher_id)
        user_obj = self.pool.get('res.users')
        user_id = user_obj.create(cr, uid, {
                'name': teacher.name,
                'login': teacher.email
                })
        teacher.write({'user_id': user_id})
        groups = []
        dataobj = self.pool['ir.model.data']
        dummy,group_id = dataobj.get_object_reference(cr, SUPERUSER_ID, 'base', 'group_portal')
        groups.append(group_id)
        dummy,group_id = dataobj.get_object_reference(cr, SUPERUSER_ID, 'school_management', 'group_school_teacher')
        groups.append(group_id)
        user_obj.write(cr, uid, [user_id], {'groups_id': [(6, 0, groups)]})
        return teacher_id
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: