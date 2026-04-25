from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class SchoolClass(models.Model):
    _name = 'school.class'
    _description = 'School Class'
    _order = 'name'

    name = fields.Char(string='Class Name', required=True)
    code = fields.Char(string='Class Code', required=True)
    level = fields.Integer(string='Level/Grade')
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)
    section_ids = fields.One2many('school.section', 'class_id', string='Sections')
    section_count = fields.Integer(compute='_compute_section_count', string='Sections')
    student_count = fields.Integer(compute='_compute_student_count', string='Students')
    teacher_id = fields.Many2one('school.teacher', string='Class Teacher')
    monthly_fee = fields.Float(string='Default Monthly Fee')
    admission_fee = fields.Float(string='Default Admission Fee')
    annual_charges = fields.Float(string='Default Annual Charges')
    subject_ids = fields.Many2many('school.subject', string='Subjects')
    academic_year = fields.Char(string='Academic Year', default=lambda self: '2025-2026')
    color = fields.Integer(string='Color')
    sequence = fields.Integer(string='Sequence', default=10)

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'Class code must be unique!'),
    ]

    @api.depends('section_ids')
    def _compute_section_count(self):
        for rec in self:
            rec.section_count = len(rec.section_ids)

    def _compute_student_count(self):
        for rec in self:
            rec.student_count = self.env['school.student'].search_count([
                ('class_id', '=', rec.id),
                ('state', '=', 'enrolled')
            ])

    def action_view_sections(self):
        return {
            'name': _('Sections'),
            'type': 'ir.actions.act_window',
            'res_model': 'school.section',
            'view_mode': 'list,form',
            'domain': [('class_id', '=', self.id)],
            'context': {'default_class_id': self.id},
        }

    def action_view_students(self):
        return {
            'name': _('Students'),
            'type': 'ir.actions.act_window',
            'res_model': 'school.student',
            'view_mode': 'list,form,kanban',
            'domain': [('class_id', '=', self.id)],
            'context': {'default_class_id': self.id},
        }
