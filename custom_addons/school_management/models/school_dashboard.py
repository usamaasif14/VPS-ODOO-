from odoo import models, fields, api, _


class SchoolDashboard(models.Model):
    _name = 'school.dashboard'
    _description = 'School Dashboard'

    name = fields.Char(default='Dashboard')

    def get_dashboard_data(self):
        Student = self.env['school.student']
        Teacher = self.env['school.teacher']
        FeeInvoice = self.env['school.fee.invoice']

        total_students = Student.search_count([('state', '=', 'enrolled')])
        total_teachers = Teacher.search_count([('state', '=', 'active')])
        total_classes = self.env['school.class'].search_count([('active', '=', True)])

        unpaid_invoices = FeeInvoice.search([('state', 'in', ('posted', 'partial'))])
        total_outstanding = sum(unpaid_invoices.mapped('amount_residual'))

        from datetime import date
        today_absent = self.env['school.attendance.line'].search_count([
            ('attendance_id.date', '=', date.today()),
            ('status', '=', 'absent'),
        ])

        return {
            'total_students': total_students,
            'total_teachers': total_teachers,
            'total_classes': total_classes,
            'total_outstanding': total_outstanding,
            'today_absent': today_absent,
        }
