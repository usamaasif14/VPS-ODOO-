from odoo import models, fields, api, _


class SchoolExam(models.Model):
    _name = 'school.exam'
    _description = 'Exam'
    _inherit = ['mail.thread']
    _order = 'date_from desc'

    name = fields.Char(string='Exam Name', required=True)
    exam_type = fields.Selection([
        ('monthly', 'Monthly Test'),
        ('mid_term', 'Mid Term'),
        ('final', 'Final Term'),
        ('annual', 'Annual Exam'),
        ('unit_test', 'Unit Test'),
    ], string='Exam Type', required=True, default='monthly')
    academic_year = fields.Char(string='Academic Year', default='2025-2026')
    date_from = fields.Date(string='Start Date', required=True)
    date_to = fields.Date(string='End Date', required=True)
    class_ids = fields.Many2many('school.class', string='Classes')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)
    description = fields.Text(string='Description')
    exam_schedule_ids = fields.One2many('school.exam.schedule', 'exam_id',
                                         string='Exam Schedule')
    result_ids = fields.One2many('school.result', 'exam_id', string='Results')
    result_count = fields.Integer(compute='_compute_result_count', string='Results')

    @api.depends('result_ids')
    def _compute_result_count(self):
        for rec in self:
            rec.result_count = len(rec.result_ids)

    def action_publish(self):
        self.write({'state': 'published'})

    def action_complete(self):
        self.write({'state': 'completed'})

    def action_view_results(self):
        return {
            'name': _('Results'),
            'type': 'ir.actions.act_window',
            'res_model': 'school.result',
            'view_mode': 'list,form',
            'domain': [('exam_id', '=', self.id)],
            'context': {'default_exam_id': self.id},
        }


class SchoolExamSchedule(models.Model):
    _name = 'school.exam.schedule'
    _description = 'Exam Schedule'
    _order = 'date, time_from'

    exam_id = fields.Many2one('school.exam', string='Exam', required=True, ondelete='cascade')
    class_id = fields.Many2one('school.class', string='Class', required=True)
    subject_id = fields.Many2one('school.subject', string='Subject', required=True)
    date = fields.Date(string='Date', required=True)
    time_from = fields.Float(string='Time From')
    time_to = fields.Float(string='Time To')
    total_marks = fields.Float(string='Total Marks', default=100.0)
    pass_marks = fields.Float(string='Pass Marks', default=33.0)
    room = fields.Char(string='Exam Room')
    invigilator_id = fields.Many2one('school.teacher', string='Invigilator')
    notes = fields.Char(string='Notes')
