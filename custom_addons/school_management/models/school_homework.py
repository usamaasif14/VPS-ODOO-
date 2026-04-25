from odoo import models, fields, api, _


class SchoolHomework(models.Model):
    _name = 'school.homework'
    _description = 'Homework'
    _inherit = ['mail.thread']
    _order = 'date desc'

    name = fields.Char(string='Title', required=True)
    class_id = fields.Many2one('school.class', string='Class', required=True)
    section_id = fields.Many2one('school.section', string='Section',
                                  domain="[('class_id','=',class_id)]")
    subject_id = fields.Many2one('school.subject', string='Subject', required=True)
    teacher_id = fields.Many2one('school.teacher', string='Assigned By', required=True)
    date = fields.Date(string='Assigned Date', required=True, default=fields.Date.today)
    due_date = fields.Date(string='Due Date', required=True)
    description = fields.Html(string='Description / Instructions')
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('assigned', 'Assigned'),
        ('completed', 'Completed'),
    ], string='Status', default='draft', tracking=True)
    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'Important'),
    ], string='Priority', default='0')
    notes = fields.Text(string='Notes')

    def action_assign(self):
        self.write({'state': 'assigned'})

    def action_send_whatsapp(self):
        self.ensure_one()
        # Get all students in this class/section
        domain = [('class_id', '=', self.class_id.id), ('state', '=', 'enrolled')]
        if self.section_id:
            domain.append(('section_id', '=', self.section_id.id))
        students = self.env['school.student'].search(domain)
        msg = (
            f"Homework Assigned!\n"
            f"Subject: {self.subject_id.name}\n"
            f"Class: {self.class_id.name}"
            f"{(' - ' + self.section_id.name) if self.section_id else ''}\n"
            f"Topic: {self.name}\n"
            f"Due Date: {self.due_date}\n"
            f"Please ensure your child completes the homework on time."
        )
        return {
            'name': _('Send Homework Notification'),
            'type': 'ir.actions.act_window',
            'res_model': 'school.whatsapp.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_student_ids': [(6, 0, students.ids)],
                'default_message': msg,
                'default_type': 'homework',
            },
        }
