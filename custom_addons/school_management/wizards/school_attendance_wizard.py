from odoo import models, fields, api, _


class SchoolAttendanceWizardStandalone(models.TransientModel):
    _name = 'school.attendance.wizard.standalone'
    _description = 'Attendance Wizard'

    class_id = fields.Many2one('school.class', string='Class', required=True)
    date = fields.Date(string='Date', required=True, default=fields.Date.today)
