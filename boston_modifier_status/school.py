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
    
class student_enroll_line(models.Model):
    _inherit = 'student.enroll.line'
    
    @api.onchange('student_id')
    def onchange_student_id(self):
        if self.student_id:
            self.std_idd = self.student_id.std_idd or ''
            
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