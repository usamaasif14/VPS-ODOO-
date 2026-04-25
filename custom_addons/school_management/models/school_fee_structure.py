from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class SchoolFeeStructure(models.Model):
    _name = 'school.fee.structure'
    _description = 'Fee Structure'
    _inherit = ['mail.thread']
    _order = 'class_id, name'

    name = fields.Char(string='Fee Structure Name', required=True)
    class_id = fields.Many2one('school.class', string='Class', required=True)
    academic_year = fields.Char(string='Academic Year', default='2025-2026', required=True)
    active = fields.Boolean(string='Active', default=True)
    description = fields.Text(string='Description')
    fee_line_ids = fields.One2many('school.fee.structure.line', 'fee_structure_id',
                                    string='Fee Lines')
    total_monthly = fields.Float(compute='_compute_totals', string='Total Monthly Fee', store=True)
    total_annual = fields.Float(compute='_compute_totals', string='Total Annual Fee', store=True)

    @api.depends('fee_line_ids', 'fee_line_ids.amount', 'fee_line_ids.fee_type')
    def _compute_totals(self):
        for rec in self:
            monthly = sum(line.amount for line in rec.fee_line_ids
                          if line.fee_type == 'monthly' and not line.optional)
            annual = sum(line.amount for line in rec.fee_line_ids
                         if line.fee_type in ('annual', 'one_time'))
            rec.total_monthly = monthly
            rec.total_annual = annual

    def action_print_fee_structure(self):
        return self.env.ref('school_management.action_report_fee_structure').report_action(self)


class SchoolFeeStructureLine(models.Model):
    _name = 'school.fee.structure.line'
    _description = 'Fee Structure Line'
    _order = 'sequence, id'

    fee_structure_id = fields.Many2one('school.fee.structure', string='Fee Structure',
                                        required=True, ondelete='cascade')
    sequence = fields.Integer(string='Sequence', default=10)
    fee_type_id = fields.Many2one('school.fee.type', string='Fee Type', required=True)
    name = fields.Char(string='Description', related='fee_type_id.name', store=True)
    fee_type = fields.Selection(related='fee_type_id.billing_type', store=True)
    amount = fields.Float(string='Amount', required=True)
    optional = fields.Boolean(string='Optional')
    taxable = fields.Boolean(string='Taxable')
    notes = fields.Char(string='Notes')


class SchoolFeeType(models.Model):
    _name = 'school.fee.type'
    _description = 'Fee Type'
    _order = 'sequence, name'

    name = fields.Char(string='Fee Type Name', required=True)
    code = fields.Char(string='Code')
    billing_type = fields.Selection([
        ('monthly', 'Monthly'),
        ('annual', 'Annual'),
        ('one_time', 'One Time'),
        ('quarterly', 'Quarterly'),
        ('exam', 'Exam Fee'),
    ], string='Billing Type', required=True, default='monthly')
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)
    sequence = fields.Integer(string='Sequence', default=10)
    account_id = fields.Many2one('account.account', string='Income Account')
