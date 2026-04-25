from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import date


class SchoolAttendance(models.Model):
    _name = 'school.attendance'
    _description = 'Student Attendance'
    _inherit = ['mail.thread']
    _order = 'date desc'

    name = fields.Char(string='Reference', compute='_compute_name', store=True)
    class_id = fields.Many2one('school.class', string='Class', required=True)
    section_id = fields.Many2one('school.section', string='Section',
                                  domain="[('class_id','=',class_id)]")
    date = fields.Date(string='Date', required=True, default=fields.Date.today)
    teacher_id = fields.Many2one('school.teacher', string='Teacher')
    subject_id = fields.Many2one('school.subject', string='Subject')
    attendance_line_ids = fields.One2many('school.attendance.line', 'attendance_id',
                                          string='Attendance Lines')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Submitted'),
    ], string='Status', default='draft', tracking=True)
    notes = fields.Text(string='Notes')
    present_count = fields.Integer(compute='_compute_counts', string='Present', store=True)
    absent_count = fields.Integer(compute='_compute_counts', string='Absent', store=True)
    late_count = fields.Integer(compute='_compute_counts', string='Late', store=True)
    total_count = fields.Integer(compute='_compute_counts', string='Total', store=True)

    @api.depends('class_id', 'section_id', 'date')
    def _compute_name(self):
        for rec in self:
            cls = rec.class_id.name if rec.class_id else ''
            sec = f"-{rec.section_id.name}" if rec.section_id else ''
            dt = rec.date.strftime('%Y-%m-%d') if rec.date else ''
            rec.name = f"ATT/{cls}{sec}/{dt}"

    @api.depends('attendance_line_ids', 'attendance_line_ids.status')
    def _compute_counts(self):
        for rec in self:
            lines = rec.attendance_line_ids
            rec.present_count = len(lines.filtered(lambda l: l.status == 'present'))
            rec.absent_count = len(lines.filtered(lambda l: l.status == 'absent'))
            rec.late_count = len(lines.filtered(lambda l: l.status == 'late'))
            rec.total_count = len(lines)

    def action_load_students(self):
        for rec in self:
            if rec.attendance_line_ids:
                raise UserError(_('Attendance lines already loaded. Reset first.'))
            domain = [('class_id', '=', rec.class_id.id), ('state', '=', 'enrolled')]
            if rec.section_id:
                domain.append(('section_id', '=', rec.section_id.id))
            students = self.env['school.student'].search(domain, order='roll_number')
            lines = [(0, 0, {
                'student_id': s.id,
                'status': 'present',
                'roll_number': s.roll_number,
            }) for s in students]
            rec.write({'attendance_line_ids': lines})

    def action_submit(self):
        self.write({'state': 'done'})

    def action_reset(self):
        self.write({'state': 'draft'})

    def action_send_absent_whatsapp(self):
        absent_students = self.attendance_line_ids.filtered(
            lambda l: l.status == 'absent'
        ).mapped('student_id')
        if not absent_students:
            raise UserError(_('No absent students found.'))
        return {
            'name': _('Notify Absent Students'),
            'type': 'ir.actions.act_window',
            'res_model': 'school.whatsapp.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_student_ids': [(6, 0, absent_students.ids)],
                'default_message': f'Your child was absent on {self.date}.',
                'default_type': 'absence',
            },
        }


class SchoolAttendanceLine(models.Model):
    _name = 'school.attendance.line'
    _description = 'Attendance Line'
    _order = 'attendance_id, roll_number'

    attendance_id = fields.Many2one('school.attendance', string='Attendance',
                                     required=True, ondelete='cascade')
    student_id = fields.Many2one('school.student', string='Student', required=True)
    roll_number = fields.Char(string='Roll No', related='student_id.roll_number', store=True)
    status = fields.Selection([
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('leave', 'On Leave'),
        ('half_day', 'Half Day'),
    ], string='Status', default='present', required=True)
    remarks = fields.Char(string='Remarks')
