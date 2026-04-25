from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SchoolFeePaymentWizard(models.TransientModel):
    _name = 'school.fee.payment.wizard'
    _description = 'Fee Payment Wizard'

    invoice_id = fields.Many2one('school.fee.invoice', string='Invoice', required=True)
    student_id = fields.Many2one('school.student', related='invoice_id.student_id',
                                  string='Student', readonly=True)
    amount_due = fields.Float(related='invoice_id.amount_residual', string='Amount Due')
    amount = fields.Float(string='Amount Paying', required=True)
    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('bank', 'Bank Transfer'),
        ('cheque', 'Cheque'),
        ('online', 'Online Payment'),
    ], string='Payment Method', required=True, default='cash')
    payment_date = fields.Date(string='Payment Date', required=True, default=fields.Date.today)
    bank_reference = fields.Char(string='Cheque / Bank Reference')
    collected_by = fields.Char(string='Collected By')
    notes = fields.Text(string='Notes')
    print_receipt = fields.Boolean(string='Print Receipt', default=True)

    def action_confirm_payment(self):
        self.ensure_one()
        if self.amount <= 0:
            raise UserError(_('Amount must be greater than zero.'))
        if self.amount > self.amount_due:
            raise UserError(_('Amount cannot exceed the balance due.'))

        payment = self.env['school.fee.payment'].create({
            'invoice_id': self.invoice_id.id,
            'date': self.payment_date,
            'amount': self.amount,
            'payment_method': self.payment_method,
            'bank_reference': self.bank_reference,
            'collected_by': self.collected_by,
            'notes': self.notes,
            'state': 'confirmed',
        })

        if self.print_receipt:
            return self.env.ref('school_management.action_report_fee_invoice').report_action(
                self.invoice_id
            )
        return {'type': 'ir.actions.act_window_close'}


class SchoolGenerateFeeWizard(models.TransientModel):
    _name = 'school.generate.fee.wizard'
    _description = 'Generate Monthly Fee Wizard'

    class_ids = fields.Many2many('school.class', string='Classes', required=True)
    fee_month = fields.Selection([
        ('1', 'January'), ('2', 'February'), ('3', 'March'),
        ('4', 'April'), ('5', 'May'), ('6', 'June'),
        ('7', 'July'), ('8', 'August'), ('9', 'September'),
        ('10', 'October'), ('11', 'November'), ('12', 'December'),
    ], string='Month', required=True)
    fee_year = fields.Char(string='Year', required=True,
                            default=lambda self: str(fields.Date.today().year))
    due_date = fields.Date(string='Due Date')
    invoice_date = fields.Date(string='Invoice Date', required=True, default=fields.Date.today)
    check_duplicate = fields.Boolean(string='Skip Duplicate', default=True,
                                      help='Skip students who already have invoice for this month/year')

    def action_generate(self):
        self.ensure_one()
        FeeInvoice = self.env['school.fee.invoice']
        created = 0
        skipped = 0

        students = self.env['school.student'].search([
            ('class_id', 'in', self.class_ids.ids),
            ('state', '=', 'enrolled'),
        ])

        for student in students:
            if self.check_duplicate:
                existing = FeeInvoice.search([
                    ('student_id', '=', student.id),
                    ('fee_month', '=', self.fee_month),
                    ('fee_year', '=', self.fee_year),
                    ('state', '!=', 'cancelled'),
                ], limit=1)
                if existing:
                    skipped += 1
                    continue

            fee_struct = student.fee_structure_id
            if not fee_struct:
                fee_struct = self.env['school.fee.structure'].search([
                    ('class_id', '=', student.class_id.id),
                    ('active', '=', True),
                ], limit=1)

            lines = []
            if fee_struct:
                for line in fee_struct.fee_line_ids.filtered(
                    lambda l: l.fee_type == 'monthly'
                ):
                    lines.append((0, 0, {
                        'fee_type_id': line.fee_type_id.id,
                        'name': line.name,
                        'amount': line.amount,
                    }))

            invoice = FeeInvoice.create({
                'student_id': student.id,
                'fee_month': self.fee_month,
                'fee_year': self.fee_year,
                'date': self.invoice_date,
                'due_date': self.due_date,
                'invoice_line_ids': lines,
                'state': 'draft',
            })
            invoice.action_post()
            created += 1

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Fee Generation Complete'),
                'message': _(f'{created} invoices created, {skipped} skipped.'),
                'type': 'success',
            },
        }
