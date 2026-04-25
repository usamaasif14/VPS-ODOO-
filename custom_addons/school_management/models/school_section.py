from odoo import models, fields, api, _


class SchoolSection(models.Model):
    _name = 'school.section'
    _description = 'School Section'
    _order = 'class_id, name'

    name = fields.Char(string='Section Name', required=True)
    code = fields.Char(string='Section Code')
    class_id = fields.Many2one('school.class', string='Class', required=True, ondelete='cascade')
    teacher_id = fields.Many2one('school.teacher', string='Section Teacher')
    capacity = fields.Integer(string='Capacity', default=40)
    active = fields.Boolean(string='Active', default=True)
    student_ids = fields.One2many('school.student', 'section_id', string='Students')
    student_count = fields.Integer(compute='_compute_student_count', string='Students')
    room_number = fields.Char(string='Room Number')
    description = fields.Text(string='Description')

    @api.depends('student_ids')
    def _compute_student_count(self):
        for rec in self:
            rec.student_count = len(rec.student_ids.filtered(lambda s: s.state == 'enrolled'))

    def name_get(self):
        result = []
        for rec in self:
            name = f"{rec.class_id.name} - {rec.name}" if rec.class_id else rec.name
            result.append((rec.id, name))
        return result

    def action_view_students(self):
        return {
            'name': _('Students'),
            'type': 'ir.actions.act_window',
            'res_model': 'school.student',
            'view_mode': 'list,form,kanban',
            'domain': [('section_id', '=', self.id)],
            'context': {'default_section_id': self.id, 'default_class_id': self.class_id.id},
        }
