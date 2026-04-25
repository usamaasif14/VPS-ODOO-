from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SchoolWhatsAppWizard(models.TransientModel):
    _name = 'school.whatsapp.wizard'
    _description = 'WhatsApp Message Wizard'

    student_ids = fields.Many2many('school.student', string='Students')
    send_to = fields.Selection([
        ('students', 'Selected Students'),
        ('class', 'Entire Class'),
        ('all', 'All Enrolled Students'),
    ], string='Send To', default='students', required=True)
    class_id = fields.Many2one('school.class', string='Class')
    section_id = fields.Many2one('school.section', string='Section',
                                  domain="[('class_id','=',class_id)]")
    mobile = fields.Char(string='Manual Number (optional)')
    message = fields.Text(string='Message', required=True)
    type = fields.Selection([
        ('fee', 'Fee Reminder'),
        ('result', 'Result'),
        ('absence', 'Absence'),
        ('homework', 'Homework'),
        ('general', 'General'),
        ('custom', 'Custom'),
    ], string='Message Type', default='general')
    use_template = fields.Boolean(string='Use Template')
    template_type = fields.Selection([
        ('fee_reminder', 'Fee Reminder'),
        ('fee_paid', 'Fee Paid Confirmation'),
        ('absent', 'Absence Notification'),
        ('holiday', 'Holiday Announcement'),
        ('exam', 'Exam Schedule'),
        ('result', 'Result Notification'),
    ], string='Template')
    config_id = fields.Many2one('school.whatsapp.config', string='WhatsApp Config',
                                 required=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        config = self.env['school.whatsapp.config'].search([('active', '=', True)], limit=1)
        if config:
            res['config_id'] = config.id
        return res

    @api.onchange('template_type')
    def _onchange_template(self):
        school_name = self.config_id.school_name if self.config_id else 'Our School'
        templates = {
            'fee_reminder': (
                f"Dear Parent,\n"
                f"This is a reminder that your child's fee is due. "
                f"Please visit {school_name} accounts to clear dues.\nThank You."
            ),
            'fee_paid': (
                f"Dear Parent,\n"
                f"We have received your fee payment. Thank You for your timely payment.\n"
                f"{school_name}"
            ),
            'absent': (
                f"Dear Parent,\n"
                f"Your child was marked absent today. Please ensure regular attendance.\n"
                f"{school_name}"
            ),
            'holiday': (
                f"Dear Parent,\n"
                f"Please note that tomorrow is a holiday. School will resume as per the schedule.\n"
                f"{school_name}"
            ),
            'exam': (
                f"Dear Parent,\n"
                f"Exams are approaching. Please ensure your child prepares well.\n"
                f"{school_name}"
            ),
            'result': (
                f"Dear Parent,\n"
                f"Your child's result is available. Please visit the school or contact us.\n"
                f"{school_name}"
            ),
        }
        if self.template_type:
            self.message = templates.get(self.template_type, '')

    def action_send(self):
        self.ensure_one()
        if not self.config_id:
            raise UserError(_('Please configure WhatsApp API first.'))

        recipients = []

        if self.send_to == 'students' and self.student_ids:
            for s in self.student_ids:
                num = s.guardian_whatsapp or s.mobile
                if num:
                    recipients.append((s, num))
        elif self.send_to == 'class' and self.class_id:
            domain = [('class_id', '=', self.class_id.id), ('state', '=', 'enrolled')]
            if self.section_id:
                domain.append(('section_id', '=', self.section_id.id))
            students = self.env['school.student'].search(domain)
            for s in students:
                num = s.guardian_whatsapp or s.mobile
                if num:
                    recipients.append((s, num))
        elif self.send_to == 'all':
            students = self.env['school.student'].search([('state', '=', 'enrolled')])
            for s in students:
                num = s.guardian_whatsapp or s.mobile
                if num:
                    recipients.append((s, num))

        if self.mobile:
            recipients.append((False, self.mobile))

        if not recipients:
            raise UserError(_('No valid WhatsApp numbers found for selected recipients.'))

        sent_count = 0
        failed_count = 0
        logs = []

        for student, number in recipients:
            success, result = self.config_id.send_whatsapp(number, self.message)
            log_vals = {
                'mobile': number,
                'message': self.message,
                'message_type': self.type,
                'state': 'sent' if success else 'failed',
                'error_message': '' if success else result,
                'provider': self.config_id.provider,
            }
            if student:
                log_vals['student_id'] = student.id
            logs.append(log_vals)
            if success:
                sent_count += 1
            else:
                failed_count += 1

        self.env['school.whatsapp.log'].create(logs)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('WhatsApp Messages Sent'),
                'message': _(f'Sent: {sent_count}, Failed: {failed_count}'),
                'type': 'success' if failed_count == 0 else 'warning',
                'sticky': False,
            },
        }
