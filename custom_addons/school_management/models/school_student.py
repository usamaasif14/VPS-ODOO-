from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date


class SchoolStudent(models.Model):
    _name = 'school.student'
    _description = 'School Student'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'
    _rec_name = 'name'

    # Basic Information
    name = fields.Char(string='Full Name', required=True, tracking=True)
    roll_number = fields.Char(string='Roll Number', readonly=True, copy=False, tracking=True)
    gr_number = fields.Char(string='GR Number', readonly=True, copy=False)
    admission_number = fields.Char(string='Admission Number', readonly=True, copy=False)
    image = fields.Binary(string='Photo', attachment=True)
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
    ], string='Gender', required=True)
    date_of_birth = fields.Date(string='Date of Birth', required=True)
    age = fields.Integer(compute='_compute_age', string='Age', store=False)
    blood_group = fields.Selection([
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
    ], string='Blood Group')
    religion = fields.Char(string='Religion')
    nationality = fields.Char(string='Nationality', default='Pakistani')
    cnic_b_form = fields.Char(string='CNIC / B-Form Number')

    # Contact
    phone = fields.Char(string='Phone')
    mobile = fields.Char(string='Mobile / WhatsApp', tracking=True)
    email = fields.Char(string='Email')
    address = fields.Text(string='Address')
    city = fields.Char(string='City')

    # Academic
    class_id = fields.Many2one('school.class', string='Class', required=True, tracking=True)
    section_id = fields.Many2one('school.section', string='Section', tracking=True,
                                  domain="[('class_id', '=', class_id)]")
    previous_school = fields.Char(string='Previous School')
    previous_class = fields.Char(string='Previous Class')
    admission_date = fields.Date(string='Admission Date', default=fields.Date.today, required=True)
    academic_year = fields.Char(string='Academic Year', default='2025-2026')

    # Guardian Information
    father_name = fields.Char(string="Father's Name", required=True)
    father_cnic = fields.Char(string="Father's CNIC")
    father_occupation = fields.Char(string="Father's Occupation")
    father_phone = fields.Char(string="Father's Phone")
    father_mobile = fields.Char(string="Father's Mobile / WhatsApp")
    father_email = fields.Char(string="Father's Email")
    mother_name = fields.Char(string="Mother's Name")
    mother_cnic = fields.Char(string="Mother's CNIC")
    mother_phone = fields.Char(string="Mother's Phone")
    guardian_name = fields.Char(string='Guardian Name')
    guardian_relation = fields.Char(string='Guardian Relation')
    guardian_phone = fields.Char(string='Guardian Phone')
    guardian_cnic = fields.Char(string='Guardian CNIC')
    guardian_whatsapp = fields.Char(string='Guardian WhatsApp', tracking=True)

    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('enrolled', 'Enrolled'),
        ('promoted', 'Promoted'),
        ('transferred', 'Transferred'),
        ('withdrawn', 'Withdrawn'),
        ('alumni', 'Alumni'),
    ], string='Status', default='draft', tracking=True)
    active = fields.Boolean(string='Active', default=True)
    leaving_certificate = fields.Boolean(string='Left Certificate Issued')
    leaving_date = fields.Date(string='Leaving Date')
    leaving_reason = fields.Text(string='Leaving Reason')

    # Fee Related
    fee_structure_id = fields.Many2one('school.fee.structure', string='Fee Structure')
    concession_type = fields.Selection([
        ('none', 'No Concession'),
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ], string='Concession Type', default='none')
    concession_value = fields.Float(string='Concession Value')
    concession_reason = fields.Text(string='Concession Reason')

    # Computed
    fee_ids = fields.One2many('school.fee.invoice', 'student_id', string='Fee Invoices')
    fee_count = fields.Integer(compute='_compute_fee_count', string='Fee Invoices')
    outstanding_balance = fields.Float(compute='_compute_outstanding_balance',
                                        string='Outstanding Balance', store=True)

    # Notes
    medical_condition = fields.Text(string='Medical Condition / Disability')
    transport_route = fields.Char(string='Transport Route')
    hostel = fields.Boolean(string='Hostel Student')
    notes = fields.Text(string='Notes')

    _sql_constraints = [
        ('roll_number_class_uniq', 'unique(roll_number, class_id)',
         'Roll number must be unique within a class!'),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('admission_number'):
                vals['admission_number'] = self.env['ir.sequence'].next_by_code('school.student') or 'STD/0001'
            if not vals.get('gr_number'):
                vals['gr_number'] = self.env['ir.sequence'].next_by_code('school.student.gr') or 'GR/0001'
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

    @api.depends('fee_ids')
    def _compute_fee_count(self):
        for rec in self:
            rec.fee_count = len(rec.fee_ids)

    @api.depends('fee_ids.state', 'fee_ids.amount_residual')
    def _compute_outstanding_balance(self):
        for rec in self:
            unpaid = rec.fee_ids.filtered(lambda f: f.state in ('posted', 'partial'))
            rec.outstanding_balance = sum(unpaid.mapped('amount_residual'))

    def action_enroll(self):
        for rec in self:
            if not rec.roll_number:
                # Auto-assign roll number based on class
                existing = self.search([
                    ('class_id', '=', rec.class_id.id),
                    ('roll_number', '!=', False),
                    ('state', '=', 'enrolled'),
                ], order='roll_number desc', limit=1)
                if existing and existing.roll_number:
                    try:
                        last_num = int(existing.roll_number.split('-')[-1])
                        rec.roll_number = f"{rec.class_id.code}-{str(last_num + 1).zfill(3)}"
                    except Exception:
                        rec.roll_number = f"{rec.class_id.code}-001"
                else:
                    rec.roll_number = f"{rec.class_id.code}-001"
            rec.state = 'enrolled'

    def action_withdraw(self):
        self.write({'state': 'withdrawn', 'active': False})

    def action_promote(self):
        self.write({'state': 'promoted'})

    def action_view_fees(self):
        return {
            'name': _('Fee Invoices'),
            'type': 'ir.actions.act_window',
            'res_model': 'school.fee.invoice',
            'view_mode': 'list,form',
            'domain': [('student_id', '=', self.id)],
            'context': {'default_student_id': self.id},
        }

    def action_view_ledger(self):
        return {
            'name': _('Student Ledger'),
            'type': 'ir.actions.act_window',
            'res_model': 'school.student.ledger',
            'view_mode': 'list',
            'domain': [('student_id', '=', self.id)],
        }

    def action_send_whatsapp(self):
        return {
            'name': _('Send WhatsApp'),
            'type': 'ir.actions.act_window',
            'res_model': 'school.whatsapp.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_student_ids': [(6, 0, self.ids)],
                'default_mobile': self.guardian_whatsapp or self.mobile,
            },
        }

    @api.onchange('class_id')
    def _onchange_class_id(self):
        self.section_id = False
        self.fee_structure_id = False
        if self.class_id:
            fee_struct = self.env['school.fee.structure'].search([
                ('class_id', '=', self.class_id.id),
                ('active', '=', True),
            ], limit=1)
            if fee_struct:
                self.fee_structure_id = fee_struct.id
