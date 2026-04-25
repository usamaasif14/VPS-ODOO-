from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date


class SchoolTeacher(models.Model):
    _name = 'school.teacher'
    _description = 'School Teacher'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(string='Full Name', required=True, tracking=True)
    employee_code = fields.Char(string='Employee Code', readonly=True, copy=False)
    image = fields.Binary(string='Photo', attachment=True)
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ], string='Gender', required=True)
    date_of_birth = fields.Date(string='Date of Birth')
    age = fields.Integer(compute='_compute_age', string='Age', store=False)
    cnic = fields.Char(string='CNIC Number')
    blood_group = fields.Selection([
        ('a+', 'A+'),
        ('a-', 'A-'),
        ('b+', 'B+'),
        ('b-', 'B-'),
        ('ab+', 'AB+'),
        ('ab-', 'AB-'),
        ('o+', 'O+'),
        ('o-', 'O-'),
    ], string='Blood Group')
    religion = fields.Char(string='Religion')
    phone = fields.Char(string='Phone', tracking=True)
    mobile = fields.Char(string='Mobile / WhatsApp', tracking=True)
    email = fields.Char(string='Email', tracking=True)
    address = fields.Text(string='Address')
    qualification = fields.Char(string='Qualification')
    specialization = fields.Char(string='Specialization')
    experience_years = fields.Integer(string='Experience (Years)')
    joining_date = fields.Date(string='Joining Date', default=fields.Date.today)
    designation = fields.Char(string='Designation', default='Teacher')
    department = fields.Char(string='Department')
    salary = fields.Float(string='Monthly Salary')
    active = fields.Boolean(string='Active', default=True)
    state = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('resigned', 'Resigned'),
    ], string='Status', default='active', tracking=True)

    subject_ids = fields.Many2many('school.subject', 'subject_teacher_rel',
                                   'teacher_id', 'subject_id', string='Subjects')
    class_ids = fields.Many2many('school.class', string='Classes Assigned')

    timetable_ids = fields.One2many('school.timetable', 'teacher_id', string='Timetable')
    whatsapp_number = fields.Char(string='WhatsApp Number')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('employee_code'):
                vals['employee_code'] = self.env['ir.sequence'].next_by_code('school.teacher') or 'TCH/0001'
        return super().create(vals_list)

    @api.depends('date_of_birth')
    def _compute_age(self):
        today = date.today()
        for rec in self:
            if rec.date_of_birth:
                rec.age = today.year - rec.date_of_birth.year - (
                    (today.month, today.day) < (rec.date_of_birth.month, rec.date_of_birth.day)
                )
            else:
                rec.age = 0

    def action_view_timetable(self):
        return {
            'name': _('Teacher Timetable'),
            'type': 'ir.actions.act_window',
            'res_model': 'school.timetable',
            'view_mode': 'list,form',
            'domain': [('teacher_id', '=', self.id)],
            'context': {'default_teacher_id': self.id},
        }
