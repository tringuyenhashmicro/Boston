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