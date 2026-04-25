from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


DAYS = [
    ('monday', 'Monday'),
    ('tuesday', 'Tuesday'),
    ('wednesday', 'Wednesday'),
    ('thursday', 'Thursday'),
    ('friday', 'Friday'),
    ('saturday', 'Saturday'),
    ('sunday', 'Sunday'),
]


class SchoolTimetable(models.Model):
    _name = 'school.timetable'
    _description = 'Class Timetable / Schedule'
    _order = 'class_id, day, period_number'

    name = fields.Char(string='Name', compute='_compute_name', store=True)
    class_id = fields.Many2one('school.class', string='Class', required=True)
    section_id = fields.Many2one('school.section', string='Section',
                                  domain="[('class_id','=',class_id)]")
    teacher_id = fields.Many2one('school.teacher', string='Teacher', required=True)
    subject_id = fields.Many2one('school.subject', string='Subject', required=True)
    day = fields.Selection(DAYS, string='Day', required=True)
    period_number = fields.Integer(string='Period No.', required=True)
    time_from = fields.Float(string='From (Time)')
    time_to = fields.Float(string='To (Time)')
    time_from_char = fields.Char(string='Start Time', compute='_compute_time_chars', store=True)
    time_to_char = fields.Char(string='End Time', compute='_compute_time_chars', store=True)
    room = fields.Char(string='Room')
    academic_year = fields.Char(string='Academic Year', default='2025-2026')
    active = fields.Boolean(string='Active', default=True)

    @api.depends('class_id', 'section_id', 'day', 'subject_id')
    def _compute_name(self):
        for rec in self:
            cls = rec.class_id.name if rec.class_id else ''
            sec = f"-{rec.section_id.name}" if rec.section_id else ''
            day = dict(DAYS).get(rec.day, '')
            sub = rec.subject_id.name if rec.subject_id else ''
            rec.name = f"{cls}{sec} | {day} | {sub}"

    @api.depends('time_from', 'time_to')
    def _compute_time_chars(self):
        for rec in self:
            rec.time_from_char = self._float_to_time(rec.time_from)
            rec.time_to_char = self._float_to_time(rec.time_to)

    @staticmethod
    def _float_to_time(value):
        if not value:
            return '00:00'
        hours = int(value)
        minutes = int((value - hours) * 60)
        return f"{hours:02d}:{minutes:02d}"

    @api.constrains('class_id', 'section_id', 'teacher_id', 'day', 'period_number')
    def _check_no_overlap_teacher(self):
        for rec in self:
            overlap = self.search([
                ('teacher_id', '=', rec.teacher_id.id),
                ('day', '=', rec.day),
                ('period_number', '=', rec.period_number),
                ('id', '!=', rec.id),
                ('active', '=', True),
            ])
            if overlap:
                raise ValidationError(
                    _(f"Teacher {rec.teacher_id.name} already has period {rec.period_number} "
                      f"on {dict(DAYS).get(rec.day)} assigned to another class!")
                )

    @api.constrains('class_id', 'section_id', 'day', 'period_number')
    def _check_no_overlap_class(self):
        for rec in self:
            domain = [
                ('class_id', '=', rec.class_id.id),
                ('day', '=', rec.day),
                ('period_number', '=', rec.period_number),
                ('id', '!=', rec.id),
                ('active', '=', True),
            ]
            if rec.section_id:
                domain.append(('section_id', '=', rec.section_id.id))
            overlap = self.search(domain)
            if overlap:
                raise ValidationError(
                    _(f"This class/section already has period {rec.period_number} "
                      f"on {dict(DAYS).get(rec.day)} assigned to another subject!")
                )
