from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SchoolResultWizard(models.TransientModel):
    _name = 'school.result.wizard'
    _description = 'Generate Results Wizard'

    exam_id = fields.Many2one('school.exam', string='Exam', required=True)
    class_id = fields.Many2one('school.class', string='Class', required=True)
    section_id = fields.Many2one('school.section', string='Section',
                                  domain="[('class_id','=',class_id)]")

    def action_generate_result_sheets(self):
        self.ensure_one()
        exam = self.exam_id
        domain = [('class_id', '=', self.class_id.id), ('state', '=', 'enrolled')]
        if self.section_id:
            domain.append(('section_id', '=', self.section_id.id))
        students = self.env['school.student'].search(domain)

        subjects = self.class_id.subject_ids
        if not subjects:
            raise UserError(_('No subjects assigned to this class.'))

        created = 0
        for student in students:
            existing = self.env['school.result'].search([
                ('exam_id', '=', exam.id),
                ('student_id', '=', student.id),
            ], limit=1)
            if existing:
                continue
            lines = [(0, 0, {
                'subject_id': subj.id,
                'max_marks': subj.total_marks,
                'pass_marks': subj.pass_marks,
                'marks_obtained': 0.0,
            }) for subj in subjects]
            self.env['school.result'].create({
                'exam_id': exam.id,
                'student_id': student.id,
                'result_line_ids': lines,
            })
            created += 1

        return {
            'name': _('Results'),
            'type': 'ir.actions.act_window',
            'res_model': 'school.result',
            'view_mode': 'list,form',
            'domain': [('exam_id', '=', exam.id), ('class_id', '=', self.class_id.id)],
        }


class SchoolAttendanceWizard(models.TransientModel):
    _name = 'school.attendance.wizard'
    _description = 'Attendance Report Wizard'

    class_id = fields.Many2one('school.class', string='Class', required=True)
    section_id = fields.Many2one('school.section', string='Section',
                                  domain="[('class_id','=',class_id)]")
    date_from = fields.Date(string='Date From', required=True)
    date_to = fields.Date(string='Date To', required=True)
    report_type = fields.Selection([
        ('summary', 'Summary'),
        ('detail', 'Detailed'),
    ], string='Report Type', default='summary', required=True)

    def action_print(self):
        data = {
            'class_id': self.class_id.id,
            'section_id': self.section_id.id if self.section_id else False,
            'date_from': str(self.date_from),
            'date_to': str(self.date_to),
            'report_type': self.report_type,
        }
        return self.env.ref('school_management.action_report_attendance').report_action(self, data=data)
