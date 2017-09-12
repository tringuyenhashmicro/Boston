# -*- coding: utf-8 -*-

from openerp import models, api, _, fields
from datetime import datetime as dt, timedelta

class school_session(models.Model):
    _name = 'school.session'
    _description = 'Session'
    
    name = fields.Char('Session Name', required=True)
    date_start = fields.Datetime('Start Time', required=True)
    date_end = fields.Datetime('End Time', required=True)
    session_location = fields.Char('Location')
    class_id = fields.Many2one('school.class', 'Class', required=True)
    recurrency = fields.Boolean('Recurrent')
    interval = fields.Integer('Repeat Every', help="Repeat every (Days/Week/Month/Year)")
    rrule_type = fields.Selection([('daily', 'Day(s)')], 'Recurrency', default='daily')
    #, ('weekly', 'Week(s)'), ('monthly', 'Month(s)'), ('yearly', 'Year(s)')
    end_type = fields.Selection([('count', 'Number of repetitions'), ('end_date', 'End date')], 'Recurrence Termination')
    count = fields.Integer('Repeat', help="Repeat x times")
    final_date = fields.Date('Repeat Until')
    mo = fields.Boolean('Mon')
    tu = fields.Boolean('Tue')
    we = fields.Boolean('Wed')
    th = fields.Boolean('Thu')
    fr = fields.Boolean('Fri')
    sa = fields.Boolean('Sat')
    su = fields.Boolean('Sun')
    starting_no = fields.Integer('Starting from Number')
    teacher_id = fields.Many2one('hr.employee', 'Teacher')
    
    
    @api.onchange('class_id')
    def _onchange_class(self):
        if self.class_id:
            self.teacher_id = self.class_id.teacher_id.id
        else:
            self.teacher_id = False

    def recursive_sessions(self, cr, uid, session, date_start, date_end, number, context=None):
        name = session.name
        if number > 0:
            name = name + ' - ' + str(number)
        session_vals = {
            'name': name,
            'date_start': date_start,
            'date_end': date_end,
            'session_location': session.session_location,
            'class_id': session.class_id.id,
            }
        session_id = self.create(cr, uid, session_vals)
        return session_id
    
    def create(self, cr, uid, vals, context=None):
        res = super(school_session, self).create(cr, uid, vals, context=context)
        session = self.browse(cr, uid, res)
        if session.recurrency:
            interval = session.interval
            if interval > 0:
                rrule_type = session.rrule_type
                if rrule_type == 'daily':
                    date_start = session.date_start
                    date_end = session.date_end
                    number = session.starting_no
                    if session.end_type == 'count':
                        for s in range(session.count):
                            date_start = dt.strptime(str(date_start), "%Y-%m-%d %H:%M:%S")+timedelta(days=interval)
                            date_end = dt.strptime(str(date_end), "%Y-%m-%d %H:%M:%S")+timedelta(days=interval)
                            self.recursive_sessions(cr, uid, session, date_start, date_end, number)
                            if number > 0:
                                number += 1
                    else:
                        date_start = dt.strptime(str(date_start), "%Y-%m-%d %H:%M:%S")+timedelta(days=interval)
                        date_end = dt.strptime(str(date_end), "%Y-%m-%d %H:%M:%S")+timedelta(days=interval)
                        final_date = dt.strptime(str(session.final_date), "%Y-%m-%d")+timedelta(days=1)
                        while date_start < final_date:
                            self.recursive_sessions(cr, uid, session, date_start, date_end, number)
                            date_start = dt.strptime(str(date_start), "%Y-%m-%d %H:%M:%S")+timedelta(days=interval)
                            date_end = dt.strptime(str(date_end), "%Y-%m-%d %H:%M:%S")+timedelta(days=interval)
                            if number > 0:
                                number += 1
        return res
    
    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        res = super(school_session, self).search(cr, uid, args=args, offset=offset, limit=limit, order=order, context=context)
        user_obj = self.pool.get('res.users')
        admin = user_obj.has_group(cr, uid, 'school_management.group_school_admin')
        teacher = user_obj.has_group(cr, uid, 'school_management.group_school_teacher')
        student = user_obj.has_group(cr, uid, 'school_management.group_school_student')
        parent = user_obj.has_group(cr, uid, 'school_management.group_school_parent')
        ids = []
        if admin:
            return res
        elif teacher:
            class_ids = self.pool.get('school.class').search(cr, uid, [('teacher_id.user_id', '=', uid)])
            args.extend([('class_id', 'in', class_ids)])
            ids = super(school_session, self).search(cr, uid, args=args, offset=offset, limit=limit, order=order, context=context)
        elif student or parent:
            enroll_line_obj = self.pool.get('student.enroll.line')
            if student:
                enroll_line_ids = enroll_line_obj.search(cr, uid, [
                    ('student_id.user_id', '=', uid), ('enroll_id.state', '=', 'enrolled')])
            else:
                student_ids = self.pool.get('school.student').search(cr, uid, [('parent_id.user_id', '=', uid)])
                enroll_line_ids = enroll_line_obj.search(cr, uid, [
                    ('student_id', 'in', student_ids), ('enroll_id.state', '=', 'enrolled')])
            if enroll_line_ids:
                class_ids = [line.enroll_id.class_id.id for line in enroll_line_obj.browse(cr, uid, enroll_line_ids)]
                args.extend([('class_id', 'in', class_ids)])
                ids = super(school_session, self).search(cr, uid, args=args, offset=offset, limit=limit, order=order, context=context)
        return ids
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: