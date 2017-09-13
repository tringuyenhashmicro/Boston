import datetime
from openerp.osv import fields, osv, orm
from openerp.tools.translate import _
from openerp import models, api, _, fields

class student_invoice(models.Model):
    _inherit = 'student.invoice'

    @api.one
    @api.depends('class_id')
    def _compute_course(self):
        self.special_dip = self.class_id.subject_id.name
        self.src_code = self.class_id.subject_id.code
        self.cer_issue = self.class_id.subject_id.cer_ib
        self.qualification = self.class_id.subject_id.cer_quali

    src_code = fields.Char('Course Code', size=256, compute='_compute_course')
    special_dip = fields.Char('Course Title', size=256, compute='_compute_course')
    cer_issue = fields.Char('Certificate Issued By', size=256, compute='_compute_course')
    qualification = fields.Char('Certification/ Qualification', size=256, compute='_compute_course')
    intake = fields.Many2one('school.class', 'Intake', invisible=True)

    @api.onchange('class_id')
    @api.depends('class_id')
    def _onchange_class(self):
        if self.class_id and self.class_id.subject_id:
            self.special_dip = self.class_id.subject_id.name
            self.src_code = self.class_id.subject_id.code
            self.cer_issue = self.class_id.subject_id.cer_ib
            self.qualification = self.class_id.subject_id.cer_quali
            self.fdate_issue = self.class_id.start_date
            self.tdate_issue = self.class_id.end_date

    @api.onchange('fdate_issue')
    @api.depends('fdate_issue', 'class_id')
    def _onchange_fdate_issue(self):
        if self.class_id:
            if self.class_id.start_date:
                start_date = datetime.datetime.strptime(self.class_id.start_date, '%Y-%m-%d')
                from_date = datetime.datetime.strptime(self.fdate_issue, '%Y-%m-%d')
                if from_date < start_date:
                    raise osv.except_osv(_('Validation Error'), _(
                        'From date should be greater than or equal to %s' % (self.class_id.start_date)))

    @api.onchange('tdate_issue')
    @api.depends('tdate_issue', 'class_id')
    def _onchange_tdate_issue(self):
        if self.class_id:
            if self.class_id.end_date:
                end_date = datetime.datetime.strptime(self.class_id.end_date, '%Y-%m-%d')
                to_date = datetime.datetime.strptime(self.tdate_issue, '%Y-%m-%d')
                if to_date > end_date:
                    raise osv.except_osv(_('Validation Error'),
                                         _('To date should be lower than or equal to %s' % (self.class_id.end_date)))
    
class school_school(models.Model):
    _inherit = 'school.school'
    
    sequence = fields.Integer('Sequence')
    company_id = fields.Many2one('res.company', 'Company', default=1)
    
class SchoolStudent(models.Model):
    _inherit = 'school.student'
    
    recruit_id = fields.Many2one('res.partner', string='Recruitment Agent')
    industi_id = fields.Many2one('res.partner', string='Industrial Partner')

class SchoolStudentLine(models.Model):
    _name = 'school.student.line'
    
    student_id = fields.Many2one('school.student', string='Student Name')
    std_idd    = fields.Char(string='Student ID', size=256, related='student_id.std_idd')
    course_id = fields.Many2many('school.school', string='Course')
    intake_id = fields.Many2many('school.class', string='Intake')
    con_from = fields.Date(string='Contract Period')
    con_to   = fields.Date(string='Contract Period To')
    name = fields.Many2one('res.partner', string='Customer')
    
class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    @api.onchange('student_id')
    @api.depends('student_id')
    def _onchange_student_id(self):
        for rc in self:
            if rc.student_id:
                if rc.student_id.recruit_id:
                    rc.is_recruit = True
                elif rc.student_id.industi_id:
                    rc.is_industrial = True
                else:
                    rc.is_recruit = False
                    rc.is_industrial = False
    line_ids = fields.One2many('school.student.line', 'name', string='Students')
    is_recruit    = fields.Boolean(string='Is a Recruitment Agent')
    is_industrial = fields.Boolean(string='Is an Industrial Partner')
    con_from = fields.Date(string='Contract Period')
    con_to   = fields.Date(string='Contract Period To')
    student_id = fields.Many2one('school.student', string='Student Name')
    std_idd    = fields.Char(string='Student ID', size=256, related='student_id.std_idd')
    course_id = fields.Many2many('school.school', string='Course')
    intake_id = fields.Many2many('school.class', string='Intake')
    
class CalendarType(models.Model):
    _name = 'calendar.type'
    name = fields.Char(string='Name', size=256)
    code = fields.Char(string='Code', size=256)

class CalendarEvent(models.Model):
    _inherit = 'calendar.event'
    
    type = fields.Selection(selection=[('leave', 'Leave'),
                             ('pub_ho','Public Holiday'),
                             ('class', 'Class'),
                             ('lead',  'Lead')], string='Type')
    type_id = fields.Many2one('calendar.type', string='Calendar Type')
    
    def update_type(self, cr, uid, vals, context=None):
        ct_obj = self.pool.get('calendar.type')
        cur_ids  = self.search(cr, uid, [])
        for vals in self.browse(cr, uid, cur_ids):
            if vals.type:
                ct_id = ct_obj.search(cr, uid, [('code', '=', vals.type)])
                ct_id = ct_id and ct_id[0] or 0
                if ct_id:
                    self.write(cr, uid, [vals.id], {'type_id': ct_id})
        return 1
    
    def update_calendar(self, cr, uid, vals, context=None):
        class_obj = self.pool.get('school.session')
        calendar_obj = self.pool.get('calendar.event')
        class_ids  = class_obj.search(cr, uid, [])
        for vals in class_obj.browse(cr, uid, class_ids):
            if vals.module_id:
                tmp_name = vals.module_id.name
            if vals.class_id:
                tmp_name = '%s, %s'%(tmp_name, vals.class_id.name)
            if vals.classroom_id:
                tmp_name = '%s, %s'%(tmp_name, vals.classroom_id.name)
            if vals.teacher_id:
                tmp_name = '%s, %s'%(tmp_name, vals.teacher_id.name)
            calendar_obj.create(cr, uid, {'name'    : tmp_name, 
                                          'start'   : vals.date_start, 
                                          'stop'    : vals.date_end,
                                          'start_date': vals.date_start, 
                                          'stop_date' : vals.date_end,
                                          'type'      :'class'})
        return 1
    
class CrmLead(models.Model):
    _inherit = 'crm.lead'
    
    def create(self, cr, uid, vals, context=None):
        calendar_obj = self.pool.get('calendar.event')
        if vals.has_key('date_action'):
            calendar_obj.create(cr, uid, {'name': vals['name'], 'type':'lead', 'start': vals['date_action'], 'stop': vals['date_action'],'start_date': vals['date_action'], 'stop_date': vals['date_action']})
        return super(CrmLead, self).create(cr, uid, vals, context=context)
    
    nric = fields.Char(string='NRIC/FIN/Passport No', size=256)
    infor_src = fields.Char(string='Info Source', size=256)
    course_inter = fields.Many2one('school.school', string='Course Interested')
    login = fields.Date(string='Log in')
    
class StudentEnrolDuedateLine(models.Model):
    _name = 'student.enrol.duedate.line'
    
    @api.model
    def get_start_date(self):
        enrl_obj = self.env['student.enroll.line']
        if self._context.has_key('enrol_id') and not self.parent_id.line_ids:
            return enrl_obj.browse(self._context['enrol_id']).enroll_id.date_start
    
    sequence = fields.Integer(string='Sequence')
    name = fields.Char(string='Name', size=256)
    parent_id = fields.Many2one('student.enroll.duedate', string='Parent')
    duedate = fields.Date(string='Due Date', default=get_start_date)
    
class student_enroll_duedate(models.Model):
    _name = 'student.enroll.duedate'
    
    @api.multi
    def validate(self):
        return 1    
    
    name = fields.Integer(string='Number of Instalment')
    enrol_id = fields.Many2one('student.enroll.line', string='Due Date')
    line_ids = fields.One2many('student.enrol.duedate.line', 'parent_id', string='Lines')
    
class student_enroll_line(models.Model):
    _inherit = 'student.enroll.line'
    
    @api.onchange('student_id')
    def onchange_student_id(self):
        if self.student_id:
            self.std_idd = self.student_id.std_idd or ''

    @api.multi
    def open_instalment_duedate(self):
        res_id = self.env['student.enroll.duedate'].search([('enrol_id', 'in', self.ids)])
        return {
            'name': 'Instalment Due Date',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'student.enroll.duedate',
            'res_id'   : res_id and res_id[0].id or False,
            'context'  : {'default_enrol_id':self.ids[0], 'default_name':self.browse(self.ids[0]).install_num},
            'target': 'new',
        }
            
    duedate_ids = fields.One2many('student.enroll.duedate', 'enrol_id', 'Due Date')
    std_idd = fields.Char(related='student_id.std_idd', string='Student ID', size=256)
    install_num = fields.Integer(string='Number of Instalment')
    

    
class StudentInvoiceLine(models.Model):
    _inherit = 'student.invoice.line'
    
    @api.one
    @api.depends('quantity', 'price_unit')
    def _subtotal(self):
        if self.install_num:
            self.subtotal = (self.quantity * self.price_unit) / self.install_num
        else:
            self.subtotal = self.quantity * self.price_unit
        
    install_num = fields.Integer(string='Number of Instalment', default=1)

class SchoolTest(models.Model):
    _inherit = 'school.test'
    
    attachment = fields.Binary('Assignment File')
    file_name = fields.Char('File Name')
    
    @api.model
    def create(self, vals):
        school_test_obj = self.env['school.test.inmo']
        stest_id = school_test_obj.search([('name','=',vals['exam_id']),
                                           ('module_id','=',vals['module_id']),
                                           ('intake_id','=',vals['class_id'])])
        if not stest_id:
            school_test_obj.create({'name': vals['exam_id'], 'module_id': vals['module_id'], 'intake_id': vals['class_id']})
        return super(SchoolTest, self).create(vals)
        
    @api.onchange('class_id','module_id')
    @api.depends('class_id','module_id')
    def _onchange_module_id(self):
        for rc in self:
            if rc.class_id and rc.module_id:
                school_test_obj = self.env['school.test.inmo']
                stest_id = school_test_obj.search([('module_id','=',rc.module_id.id),
                                                   ('intake_id','=',rc.class_id.id)])
                if stest_id:
                    rc.exam_id = school_test_obj.browse(stest_id[0].id).name.id
    
    module_id = fields.Many2one('school.module', string='Module')

class SchoolTestInmo(models.Model):
    _name = 'school.test.inmo'
    name = fields.Many2one('school.exam', string='Tests Types')
    module_id = fields.Many2one('school.module', string='Module')
    intake_id = fields.Many2one('school.class', string='Intake')

class HrEmployeeLine(models.Model):
    _name = 'hr.employee.line'
    
    name = fields.Char('Name', size=256)
    trainee = fields.Many2one('hr.employee', string='Trainees')
    trainer = fields.Many2one('res.partner', string='Trainer')
    dateorder = fields.Date(string='Date')
    department = fields.Many2one('hr.department', string='Department')
    course_tit = fields.Many2one('employee.training', string='Course Title')
    course_duhr = fields.Float(string='Course Duration in Hrs', digits=(12,1))
    course_fees = fields.Float(string='Course Fees')
    train_type  = fields.Selection(selection=[('Internal','Internal'),('External','External')], string='Type of Training')
    remark = fields.Text('Remarks')
    emp_id = fields.Many2one('hr.employee', 'Employee')
    
class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    
    training_records = fields.One2many('hr.employee.line', 'trainee', string='Employee')
    empt_type = fields.Selection(selection=[('Employee', 'Employee'),
                                            ('Training', 'Training Record')], string='Type of Employees')
    
class StudentEnroll(models.Model):
    _inherit = 'student.enroll'
    
    @api.multi
    def action_enroll(self):
        inv_obj = self.env['student.invoice']
        std_class = self.class_id
        std_course = std_class.subject_id
        fees = []
        if len(std_course.enroll_fee_ids) == 1:
            fees += [std_course.enroll_fee_ids]
        else:
            fees += std_course.enroll_fee_ids
        lines = []
        total_untax = 0
        for fee in fees:
            for line in fee:
                if fee.amount > 0 and fee.category_id.name == 'Course Fee':
                    lines.append((0, 1, {
                        'name': line.fee_id.name,
                        'quantity': 1,
                        'price_unit': line.amount,
                        'cunit_price': str(line.amount),                        
                        'std_invoice_line_tax_id': line.tax_ids and [(4,[x.id for x in line.tax_ids ])] or [],
                    }))
                    total_untax += line.amount
        if lines:
            inv_parent = {}
            for line in self.line_ids:
                student_id = line.student_id.id
                parent_id = line.student_id.parent_id and line.student_id.parent_id.id or False
                for inv_line in lines:
                    inv_line[2].update({'student_id': student_id, 'install_num': line.install_num,})
                inv_vals = {
                    'student_id': student_id,
                    'bill_to': '%s %s'%(line.student_id.name,line.student_id.l_name and line.student_id.l_name or ''),
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
        total_invoice = 0
        for invoice in self.invoice_ids:
            invoice.fdate_issue = self.date_start
            invoice.tdate_issue = self.date_end
            total_invoice += invoice.untax_amount
            if not invoice.enroll_no:
                invoice.enroll_no = self.env['ir.sequence'].get('enroll.no') or '/'
            # Checking these invoices are full amount or not. if full, we will make this enroll done
        if total_untax == total_invoice:
            self.state = 'enrolled'
        else:
            self.action_enroll()