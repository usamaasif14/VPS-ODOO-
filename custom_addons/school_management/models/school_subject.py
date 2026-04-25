from odoo import models, fields, api, _


class SchoolSubject(models.Model):
    _name = 'school.subject'
    _description = 'School Subject'
    _order = 'name'

    name = fields.Char(string='Subject Name', required=True)
    code = fields.Char(string='Subject Code', required=True)
    subject_type = fields.Selection([
        ('compulsory', 'Compulsory'),
        ('elective', 'Elective'),
        ('co_curricular', 'Co-Curricular'),
    ], string='Subject Type', default='compulsory', required=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)
    credit_hours = fields.Float(string='Credit Hours', default=1.0)
    pass_marks = fields.Float(string='Pass Marks', default=33.0)
    total_marks = fields.Float(string='Total Marks', default=100.0)
    teacher_ids = fields.Many2many('school.teacher', 'subject_teacher_rel',
                                   'subject_id', 'teacher_id', string='Teachers')
    class_ids = fields.Many2many('school.class', string='Classes')
    color = fields.Integer(string='Color')

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'Subject code must be unique!'),
    ]
