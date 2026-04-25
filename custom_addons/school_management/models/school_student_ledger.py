from odoo import models, fields, api, _


class SchoolStudentLedger(models.Model):
    _name = 'school.student.ledger'
    _description = 'Student Ledger'
    _order = 'date asc, id asc'

    student_id = fields.Many2one('school.student', string='Student',
                                  required=True, ondelete='cascade')
    class_id = fields.Many2one('school.class', related='student_id.class_id',
                                string='Class', store=True)
    date = fields.Date(string='Date', required=True, default=fields.Date.today)
    description = fields.Char(string='Description', required=True)
    type = fields.Selection([
        ('invoice', 'Invoice'),
        ('payment', 'Payment'),
        ('concession', 'Concession'),
        ('adjustment', 'Adjustment'),
    ], string='Type', required=True, default='invoice')
    debit = fields.Float(string='Debit (Dr)')
    credit = fields.Float(string='Credit (Cr)')
    balance = fields.Float(compute='_compute_balance', string='Balance', store=False)
    running_balance = fields.Float(string='Running Balance')
    reference = fields.Char(string='Reference')
    invoice_id = fields.Many2one('school.fee.invoice', string='Invoice')
    academic_year = fields.Char(string='Academic Year', default='2025-2026')

    @api.depends('debit', 'credit')
    def _compute_balance(self):
        for rec in self:
            rec.balance = rec.debit - rec.credit

    @api.model
    def get_student_ledger(self, student_id, date_from=None, date_to=None):
        domain = [('student_id', '=', student_id)]
        if date_from:
            domain.append(('date', '>=', date_from))
        if date_to:
            domain.append(('date', '<=', date_to))
        records = self.search(domain, order='date asc, id asc')
        running = 0.0
        for rec in records:
            running += rec.debit - rec.credit
            rec.running_balance = running
        return records
