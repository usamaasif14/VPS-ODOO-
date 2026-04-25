from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class SchoolResult(models.Model):
    _name = 'school.result'
    _description = 'Student Result'
    _order = 'exam_id, student_id'

    exam_id = fields.Many2one('school.exam', string='Exam', required=True)
    student_id = fields.Many2one('school.student', string='Student', required=True)
    class_id = fields.Many2one('school.class', related='student_id.class_id',
                                string='Class', store=True)
    section_id = fields.Many2one('school.section', related='student_id.section_id',
                                  string='Section', store=True)
    roll_number = fields.Char(related='student_id.roll_number', string='Roll No', store=True)
    academic_year = fields.Char(string='Academic Year', default='2025-2026')
    result_line_ids = fields.One2many('school.result.line', 'result_id',
                                       string='Subject Results')
    total_marks_obtained = fields.Float(compute='_compute_totals',
                                         string='Total Marks Obtained', store=True)
    total_max_marks = fields.Float(compute='_compute_totals', string='Total Max Marks', store=True)
    percentage = fields.Float(compute='_compute_totals', string='Percentage %', store=True)
    grade = fields.Char(compute='_compute_grade', string='Grade', store=True)
    result_status = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('detained', 'Detained'),
    ], compute='_compute_grade', string='Result', store=True)
    position = fields.Integer(string='Position / Rank')
    remarks = fields.Text(string='Remarks')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('published', 'Published'),
    ], string='Status', default='draft')

    @api.depends('result_line_ids', 'result_line_ids.marks_obtained',
                 'result_line_ids.max_marks')
    def _compute_totals(self):
        for rec in self:
            obtained = sum(rec.result_line_ids.mapped('marks_obtained'))
            max_marks = sum(rec.result_line_ids.mapped('max_marks'))
            rec.total_marks_obtained = obtained
            rec.total_max_marks = max_marks
            rec.percentage = (obtained / max_marks * 100) if max_marks else 0.0

    @api.depends('percentage', 'result_line_ids.is_pass')
    def _compute_grade(self):
        for rec in self:
            pct = rec.percentage
            any_fail = any(not l.is_pass for l in rec.result_line_ids)
            if pct >= 90:
                rec.grade = 'A+'
            elif pct >= 80:
                rec.grade = 'A'
            elif pct >= 70:
                rec.grade = 'B'
            elif pct >= 60:
                rec.grade = 'C'
            elif pct >= 50:
                rec.grade = 'D'
            elif pct >= 33:
                rec.grade = 'E'
            else:
                rec.grade = 'F'
            rec.result_status = 'fail' if (pct < 33 or any_fail) else 'pass'

    def action_publish(self):
        self.write({'state': 'published'})

    def action_print_result_card(self):
        return self.env.ref('school_management.action_report_result_card').report_action(self)

    def action_send_whatsapp(self):
        self.ensure_one()
        mobile = self.student_id.guardian_whatsapp or self.student_id.mobile
        msg = (
            f"Dear Parent of {self.student_id.name},\n"
            f"Exam: {self.exam_id.name}\n"
            f"Marks: {self.total_marks_obtained}/{self.total_max_marks}\n"
            f"Percentage: {self.percentage:.1f}%\n"
            f"Grade: {self.grade} | Result: {self.result_status.upper()}\n"
        )
        return {
            'name': _('Send Result via WhatsApp'),
            'type': 'ir.actions.act_window',
            'res_model': 'school.whatsapp.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_mobile': mobile,
                'default_message': msg,
                'default_student_ids': [(6, 0, [self.student_id.id])],
            },
        }


class SchoolResultLine(models.Model):
    _name = 'school.result.line'
    _description = 'Result Line'
    _order = 'sequence, subject_id'

    result_id = fields.Many2one('school.result', string='Result',
                                 required=True, ondelete='cascade')
    sequence = fields.Integer(string='Seq', default=10)
    subject_id = fields.Many2one('school.subject', string='Subject', required=True)
    max_marks = fields.Float(string='Max Marks', default=100.0)
    pass_marks = fields.Float(string='Pass Marks', default=33.0)
    marks_obtained = fields.Float(string='Marks Obtained')
    is_pass = fields.Boolean(compute='_compute_pass', string='Pass', store=True)
    grade = fields.Char(compute='_compute_grade', string='Grade', store=True)
    remarks = fields.Char(string='Remarks')

    @api.depends('marks_obtained', 'pass_marks')
    def _compute_pass(self):
        for rec in self:
            rec.is_pass = rec.marks_obtained >= rec.pass_marks

    @api.depends('marks_obtained', 'max_marks')
    def _compute_grade(self):
        for rec in self:
            if not rec.max_marks:
                rec.grade = '-'
                continue
            pct = (rec.marks_obtained / rec.max_marks) * 100
            if pct >= 90:
                rec.grade = 'A+'
            elif pct >= 80:
                rec.grade = 'A'
            elif pct >= 70:
                rec.grade = 'B'
            elif pct >= 60:
                rec.grade = 'C'
            elif pct >= 50:
                rec.grade = 'D'
            elif pct >= 33:
                rec.grade = 'E'
            else:
                rec.grade = 'F'
