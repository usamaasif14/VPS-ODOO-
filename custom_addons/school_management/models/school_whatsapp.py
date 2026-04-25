from odoo import models, fields, api, _
import requests
import json
import logging

_logger = logging.getLogger(__name__)


class SchoolWhatsApp(models.Model):
    _name = 'school.whatsapp.log'
    _description = 'WhatsApp Message Log'
    _order = 'date desc'

    name = fields.Char(string='Reference', compute='_compute_name', store=True)
    date = fields.Datetime(string='Date Sent', default=fields.Datetime.now)
    mobile = fields.Char(string='To (Mobile)')
    student_id = fields.Many2one('school.student', string='Student')
    message = fields.Text(string='Message')
    message_type = fields.Selection([
        ('fee', 'Fee Reminder'),
        ('result', 'Result Notification'),
        ('absence', 'Absence Alert'),
        ('homework', 'Homework'),
        ('general', 'General'),
        ('custom', 'Custom'),
    ], string='Type', default='general')
    state = fields.Selection([
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('pending', 'Pending'),
    ], string='Status', default='pending')
    error_message = fields.Text(string='Error')
    provider = fields.Selection([
        ('whatsapp_api', 'WhatsApp Business API'),
        ('twilio', 'Twilio'),
        ('ultramsg', 'UltraMsg'),
        ('wa_gateway', 'WA Gateway'),
    ], string='Provider')

    @api.depends('student_id', 'date')
    def _compute_name(self):
        for rec in self:
            student = rec.student_id.name if rec.student_id else 'N/A'
            dt = rec.date.strftime('%Y-%m-%d %H:%M') if rec.date else ''
            rec.name = f"WA/{student}/{dt}"


class SchoolWhatsAppConfig(models.Model):
    _name = 'school.whatsapp.config'
    _description = 'WhatsApp API Configuration'

    name = fields.Char(string='Configuration Name', required=True, default='WhatsApp Config')
    provider = fields.Selection([
        ('ultramsg', 'UltraMsg'),
        ('twilio', 'Twilio'),
        ('whatsapp_api', 'WhatsApp Business API'),
        ('wa_gateway', 'Custom WA Gateway'),
    ], string='API Provider', required=True, default='ultramsg')
    api_url = fields.Char(string='API URL / Endpoint')
    api_token = fields.Char(string='API Token / Key')
    instance_id = fields.Char(string='Instance ID')
    account_sid = fields.Char(string='Account SID (Twilio)')
    auth_token = fields.Char(string='Auth Token (Twilio)')
    from_number = fields.Char(string='WhatsApp From Number (with country code)')
    active = fields.Boolean(string='Active', default=True)
    school_name = fields.Char(string='School Name', required=True)
    school_phone = fields.Char(string='School Phone')
    school_address = fields.Text(string='School Address')
    school_logo = fields.Binary(string='School Logo', attachment=True)

    def send_whatsapp(self, mobile, message):
        """Send WhatsApp message using configured provider."""
        self.ensure_one()
        if not mobile:
            return False, "No mobile number provided"

        # Clean number
        number = ''.join(filter(lambda x: x.isdigit() or x == '+', mobile))
        if not number.startswith('+'):
            # Assume Pakistan if no country code
            if number.startswith('0'):
                number = '+92' + number[1:]
            else:
                number = '+92' + number

        try:
            if self.provider == 'ultramsg':
                return self._send_ultramsg(number, message)
            elif self.provider == 'twilio':
                return self._send_twilio(number, message)
            elif self.provider == 'wa_gateway':
                return self._send_gateway(number, message)
            else:
                return False, "Provider not configured"
        except Exception as e:
            _logger.error("WhatsApp send error: %s", str(e))
            return False, str(e)

    def _send_ultramsg(self, number, message):
        """UltraMsg WhatsApp API."""
        url = f"https://api.ultramsg.com/{self.instance_id}/messages/chat"
        payload = {
            "token": self.api_token,
            "to": number,
            "body": message,
            "priority": 10,
        }
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        response = requests.post(url, data=payload, headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data.get('sent') == 'true':
                return True, "Sent"
            return False, data.get('error', 'Unknown error')
        return False, f"HTTP {response.status_code}"

    def _send_twilio(self, number, message):
        """Twilio WhatsApp API."""
        url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"
        payload = {
            "To": f"whatsapp:{number}",
            "From": f"whatsapp:{self.from_number}",
            "Body": message,
        }
        response = requests.post(
            url, data=payload,
            auth=(self.account_sid, self.auth_token), timeout=15
        )
        if response.status_code in (200, 201):
            return True, "Sent"
        return False, f"HTTP {response.status_code}"

    def _send_gateway(self, number, message):
        """Custom WA Gateway."""
        headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json',
        }
        payload = {'phone': number, 'message': message}
        response = requests.post(self.api_url, json=payload, headers=headers, timeout=15)
        if response.status_code in (200, 201):
            return True, "Sent"
        return False, f"HTTP {response.status_code}"
