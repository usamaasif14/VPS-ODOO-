from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import date, datetime


MONTHS = [
    ('1', 'January'), ('2', 'February'), ('3', 'March'),
    ('4', 'April'), ('5', 'May'), ('6', 'June'),
    ('7', 'July'), ('8', 'August'), ('9', 'September'),
    ('10', 'October'), ('11', 'November'), ('12', 'December'),
]


class SchoolFeeInvoice(models.Model):
    _name = 'school.fee.invoice'
    _description = 'Student Fee Invoice'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, name desc'

    name = fields.Char(string='Invoice Number', readonly=True, copy=False)
    student_id = fields.Many2one('school.student', string='Student', required=True, tracking=True)
    class_id = fields.Many2one('school.class', string='Class',
                                related='student_id.class_id', store=True)
    section_id = fields.Many2one('school.section', string='Section',
                                  related='student_id.section_id', store=True)
    roll_number = fields.Char(string='Roll Number',
                               related='student_id.roll_number', store=True)
    fee_month = fields.Selection(MONTHS, string='Fee Month', tracking=True)
    fee_year = fields.Char(string='Fee Year', default=lambda self: str(date.today().year))
    academic_year = fields.Char(string='Academic Year', default='2025-2026')
    date = fields.Date(string='Invoice Date', default=fields.Date.today, required=True)
    due_date = fields.Date(string='Due Date')

    invoice_line_ids = fields.One2many('school.fee.invoice.line', 'invoice_id',
                                        string='Invoice Lines')
    amount_total = fields.Float(compute='_compute_amounts', string='Total Amount', store=True)
    amount_paid = fields.Float(compute='_compute_amounts', string='Amount Paid', store=True)
    amount_residual = fields.Float(compute='_compute_amounts', string='Balance Due', store=True)
    concession_amount = fields.Float(string='Concession / Discount')
    late_fee = fields.Float(string='Late Fee')
    notes = fields.Text(string='Notes')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Unpaid'),
        ('partial', 'Partially Paid'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)

    payment_ids = fields.One2many('school.fee.payment', 'invoice_id', string='Payments')
    payment_date = fields.Date(string='Last Payment Date')
    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('bank', 'Bank Transfer'),
        ('cheque', 'Cheque'),
        ('online', 'Online Payment'),
    ], string='Payment Method')
    receipt_number = fields.Char(string='Receipt Number')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals['name'] == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('school.fee.invoice') or 'FEE/0001'
        return super().create(vals_list)

    @api.depends('invoice_line_ids.amount', 'concession_amount', 'late_fee', 'payment_ids.amount')
    def _compute_amounts(self):
        for rec in self:
            subtotal = sum(line.amount for line in rec.invoice_line_ids)
            total = subtotal - rec.concession_amount + rec.late_fee
            paid = sum(p.amount for p in rec.payment_ids if p.state == 'confirmed')
            rec.amount_total = total
            rec.amount_paid = paid
            rec.amount_residual = total - paid

    def action_post(self):
        for rec in self:
            if not rec.invoice_line_ids:
                raise UserError(_('Cannot confirm an invoice with no lines.'))
            rec.state = 'posted'
            # Create ledger entry
            self.env['school.student.ledger'].create({
                'student_id': rec.student_id.id,
                'date': rec.date,
                'description': f'Fee Invoice - {rec.name}',
                'debit': rec.amount_total,
                'credit': 0.0,
                'reference': rec.name,
                'invoice_id': rec.id,
                'type': 'invoice',
            })

    def action_register_payment(self):
        return {
            'name': _('Register Payment'),
            'type': 'ir.actions.act_window',
            'res_model': 'school.fee.payment.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_invoice_id': self.id,
                'default_amount': self.amount_residual,
                'default_student_id': self.student_id.id,
            },
        }

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_reset_draft(self):
        self.write({'state': 'draft'})

    def action_print_invoice(self):
        return self.env.ref('school_management.action_report_fee_invoice').report_action(self)

    def action_send_whatsapp(self):
        self.ensure_one()
        mobile = self.student_id.guardian_whatsapp or self.student_id.mobile
        message = (
            f"Dear Parent of {self.student_id.name},\n"
            f"Fee Invoice: {self.name}\n"
            f"Month: {dict(MONTHS).get(self.fee_month, '')} {self.fee_year}\n"
            f"Amount: {self.amount_total:,.2f}\n"
            f"Paid: {self.amount_paid:,.2f}\n"
            f"Balance: {self.amount_residual:,.2f}\n"
            f"Please pay your fee on time.\nThank You."
        )
        return {
            'name': _('Send WhatsApp'),
            'type': 'ir.actions.act_window',
            'res_model': 'school.whatsapp.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_mobile': mobile,
                'default_message': message,
                'default_student_ids': [(6, 0, [self.student_id.id])],
            },
        }

    def _update_payment_state(self):
        for rec in self:
            if rec.amount_residual <= 0:
                rec.state = 'paid'
            elif rec.amount_paid > 0:
                rec.state = 'partial'


class SchoolFeeInvoiceLine(models.Model):
    _name = 'school.fee.invoice.line'
    _description = 'Fee Invoice Line'
    _order = 'sequence, id'

    invoice_id = fields.Many2one('school.fee.invoice', string='Invoice',
                                  required=True, ondelete='cascade')
    sequence = fields.Integer(string='Sequence', default=10)
    fee_type_id = fields.Many2one('school.fee.type', string='Fee Type', required=True)
    name = fields.Char(string='Description', required=True)
    amount = fields.Float(string='Amount', required=True)
    concession = fields.Float(string='Concession')
    net_amount = fields.Float(compute='_compute_net', string='Net Amount', store=True)

    @api.depends('amount', 'concession')
    def _compute_net(self):
        for rec in self:
            rec.net_amount = rec.amount - rec.concession

    @api.onchange('fee_type_id')
    def _onchange_fee_type(self):
        if self.fee_type_id:
            self.name = self.fee_type_id.name


class SchoolFeePayment(models.Model):
    _name = 'school.fee.payment'
    _description = 'Fee Payment'
    _inherit = ['mail.thread']
    _order = 'date desc'

    name = fields.Char(string='Receipt Number', readonly=True, copy=False)
    invoice_id = fields.Many2one('school.fee.invoice', string='Invoice', required=True)
    student_id = fields.Many2one('school.student', related='invoice_id.student_id',
                                  string='Student', store=True)
    date = fields.Date(string='Payment Date', default=fields.Date.today, required=True)
    amount = fields.Float(string='Amount Paid', required=True)
    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('bank', 'Bank Transfer'),
        ('cheque', 'Cheque'),
        ('online', 'Online Payment'),
    ], string='Payment Method', default='cash', required=True)
    bank_reference = fields.Char(string='Bank/Cheque Reference')
    collected_by = fields.Char(string='Collected By')
    notes = fields.Text(string='Notes')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='confirmed', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name'):
                vals['name'] = self.env['ir.sequence'].next_by_code('school.fee.payment') or 'RCP/0001'
        records = super().create(vals_list)
        for rec in records:
            rec.invoice_id._update_payment_state()
            # Ledger credit entry
            self.env['school.student.ledger'].create({
                'student_id': rec.student_id.id,
                'date': rec.date,
                'description': f'Payment - {rec.name}',
                'debit': 0.0,
                'credit': rec.amount,
                'reference': rec.name,
                'invoice_id': rec.invoice_id.id,
                'type': 'payment',
            })
        return records
