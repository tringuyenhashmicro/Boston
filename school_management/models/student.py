# -*- coding: utf-8 -*-

from openerp import SUPERUSER_ID, models, api, _, fields

class school_student(models.Model):
    _name = 'school.student'
    _description = 'Student'
    
    name = fields.Char('First Name', required=True)
    l_name = fields.Char('Last Name')
    image = fields.Binary('Photo')
    birth_date = fields.Date('Date of Birth')
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], 'Gender')
    bill_parent = fields.Boolean('Bill to Parent')
    is_parent = fields.Boolean('Is a Parent')
    child_ids = fields.One2many('school.student', 'parent_id', 'Children')
    email = fields.Char('Email')
    user_id = fields.Many2one('res.users', 'Related User')
    nationality = fields.Char('Nationality')
    nric = fields.Char('NRIC/Passport No/Fin No', size=256)
    religion = fields.Many2one('school.religion', string='Religion')
    married = fields.Selection([('single', 'Single'),
                                ('married', 'Married')], string='Marital Status')
    occupation = fields.Text('Occupation')
    address = fields.Text('Adress')
    home_tel = fields.Char('Home Tel. No', size=256)
    office_tel = fields.Char('Office Tel. No', size=256)
    handfone = fields.Char('Handphone No')
    emer_name = fields.Char('Name')
    relationship = fields.Char('Relationship', size=256)
    emer_addres  = fields.Text('Address')
    emer_ocupation = fields.Text('Occupation')
    emer_hometel   = fields.Char('Home Tel. No', size=256)
    emer_office_tel = fields.Char('Office Tel. No', size=256)
    emer_handfone = fields.Char('Handphone No')
    emer_email = fields.Char('Email')
    
    def write(self, cr, uid, ids, vals, context=None):
        res = super(school_student, self).write(cr, uid, ids, vals, context=context)
        for student in self.browse(cr, uid, ids):
            if student.is_parent or not 'no_user' in context:
                if student.user_id:
                    student.user_id.write({'name': student.name, 'email': student.email})
                else:
                    user_id = self.pool.get('res.users').create(cr, uid, {
                        'name': student.name,
                        'login': student.email
                        }) 
                    student.write({'user_id': user_id})
        return res
    
    def create(self, cr, uid, vals, context=None):
        student_id = super(school_student, self).create(cr, uid, vals, context=context)
        student = self.browse(cr, uid, student_id)
        # Add group student for user
        obj_data = self.pool.get('ir.model.data')
        student_group = obj_data.get_object_reference(cr, uid, 'school_management', 'group_school_student')
        student_group = student_group and student_group[1] or 0        
        if student.is_parent or not 'no_user' in context or not vals.has_key('user_id'):
            print '++++++++   co nhay vo truong hop nay    ++++++++  '
            user_obj = self.pool.get('res.users')
            user_id = user_obj.create(cr, uid, {
                    'name': student.name,
                    'login': student.email,
                    'no_share': True,
                    'groups_id': [(6, 0, [student_group])] 
                    })
            student.write({'user_id': user_id})
            groups = []
            dataobj = self.pool['ir.model.data']
            dummy,group_id = dataobj.get_object_reference(cr, SUPERUSER_ID, 'base', 'group_portal')
            groups.append(group_id)
            if student.is_parent:
                dummy,group_id = dataobj.get_object_reference(cr, SUPERUSER_ID, 'school_management', 'group_school_parent')
                groups.append(group_id)
            else:
                dummy,group_id = dataobj.get_object_reference(cr, SUPERUSER_ID, 'school_management', 'group_school_student')
                groups.append(group_id)
            print 'gia tri cua group ne   ++++    ', groups
            user_obj.write(cr, uid, [user_id], {'groups_id': [(6, 0, groups)]})
        return student_id

class school_student_parent(models.Model):
    _inherit = 'school.student'
    
    parent_id = fields.Many2one('school.student', 'Parent', domain=[('is_parent', '=', True)])
    
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: