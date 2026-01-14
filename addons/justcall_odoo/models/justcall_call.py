# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class JustCallCall(models.Model):
    _name = 'justcall.call'
    _description = 'JustCall Call Log'
    _order = 'call_date desc'
    _rec_name = 'display_name'

    # JustCall fields
    justcall_call_id = fields.Char(
        string="JustCall Call ID",
        required=True,
        index=True,
        help="Unique identifier from JustCall",
    )
    justcall_user_id = fields.Char(
        string="JustCall User ID",
        help="JustCall user who made/received the call",
    )
    justcall_user_email = fields.Char(
        string="JustCall User Email",
        help="Email of JustCall user",
    )
    
    # Call details
    call_date = fields.Datetime(
        string="Call Date",
        required=True,
        index=True,
    )
    direction = fields.Selection(
        [
            ('inbound', 'Inbound'),
            ('outbound', 'Outbound'),
        ],
        string="Direction",
        required=True,
    )
    status = fields.Selection(
        [
            ('completed', 'Completed'),
            ('no-answer', 'No Answer'),
            ('busy', 'Busy'),
            ('failed', 'Failed'),
            ('cancelled', 'Cancelled'),
        ],
        string="Status",
        default='completed',
    )
    duration = fields.Integer(
        string="Duration (seconds)",
        help="Call duration in seconds",
    )
    duration_formatted = fields.Char(
        string="Duration",
        compute='_compute_duration_formatted',
    )
    
    # Phone numbers
    from_number = fields.Char(
        string="From Number",
        help="Caller's phone number",
    )
    to_number = fields.Char(
        string="To Number",
        help="Recipient's phone number",
    )
    contact_number = fields.Char(
        string="Contact Number",
        compute='_compute_contact_number',
        store=True,
        help="Normalized contact phone number",
    )
    
    # Relationships
    partner_id = fields.Many2one(
        'res.partner',
        string="Contact",
        ondelete='set null',
        help="Matched contact from phone number",
    )
    lead_id = fields.Many2one(
        'crm.lead',
        string="Lead",
        ondelete='set null',
        help="Matched lead from phone number",
    )
    project_id = fields.Many2one(
        'project.project',
        string="Project",
        ondelete='set null',
        help="Matched project from contact or lead",
    )
    user_id = fields.Many2one(
        'res.users',
        string="Odoo User",
        help="Odoo user mapped from JustCall user",
    )
    
    # Recording and notes
    recording_url = fields.Char(
        string="Recording URL",
        help="Link to call recording",
    )
    recording_duration = fields.Integer(
        string="Recording Duration (seconds)",
    )
    notes = fields.Text(
        string="Notes",
        help="Call notes or transcription",
    )
    transcription = fields.Text(
        string="Transcription",
        help="Call transcription if available",
    )
    
    # Additional metadata
    cost = fields.Float(
        string="Cost",
        help="Call cost if available",
    )
    tags = fields.Char(
        string="Tags",
        help="Call tags from JustCall",
    )
    raw_data = fields.Text(
        string="Raw Data",
        help="Raw webhook data for debugging",
    )
    
    # Display
    display_name = fields.Char(
        string="Display Name",
        compute='_compute_display_name',
    )

    _sql_constraints = [
        ('unique_justcall_call_id', 'unique(justcall_call_id)',
         'Call ID must be unique!'),
    ]

    @api.depends('duration')
    def _compute_duration_formatted(self):
        """Format duration as MM:SS"""
        for call in self:
            if call.duration:
                minutes = call.duration // 60
                seconds = call.duration % 60
                call.duration_formatted = f"{minutes:02d}:{seconds:02d}"
            else:
                call.duration_formatted = "00:00"

    @api.depends('direction', 'from_number', 'to_number')
    def _compute_contact_number(self):
        """Determine contact number based on call direction"""
        for call in self:
            if call.direction == 'inbound':
                call.contact_number = call.from_number
            else:
                call.contact_number = call.to_number

    @api.depends('partner_id', 'lead_id', 'project_id', 'call_date', 'direction')
    def _compute_display_name(self):
        """Generate display name"""
        for call in self:
            name_parts = []
            if call.partner_id:
                name_parts.append(call.partner_id.name)
            elif call.lead_id:
                name_parts.append(call.lead_id.name)
            elif call.project_id:
                name_parts.append(call.project_id.name)
            else:
                name_parts.append(call.contact_number or _("Unknown"))
            
            name_parts.append(f"({call.direction})")
            name_parts.append(call.call_date.strftime('%Y-%m-%d %H:%M') if call.call_date else "")
            
            call.display_name = " - ".join(filter(None, name_parts))

    def action_open_partner(self):
        """Open related partner"""
        self.ensure_one()
        if not self.partner_id:
            raise UserError(_("No contact associated with this call"))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Contact'),
            'res_model': 'res.partner',
            'res_id': self.partner_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_open_lead(self):
        """Open related lead"""
        self.ensure_one()
        if not self.lead_id:
            raise UserError(_("No lead associated with this call"))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Lead'),
            'res_model': 'crm.lead',
            'res_id': self.lead_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_open_project(self):
        """Open related project"""
        self.ensure_one()
        if not self.project_id:
            raise UserError(_("No project associated with this call"))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Project'),
            'res_model': 'project.project',
            'res_id': self.project_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_open_recording(self):
        """Open call recording in browser"""
        self.ensure_one()
        if not self.recording_url:
            raise UserError(_("No recording available for this call"))
        return {
            'type': 'ir.actions.act_url',
            'url': self.recording_url,
            'target': 'new',
        }

    @api.model
    def create_from_webhook(self, webhook_data):
        """Create or update call record from webhook data"""
        justcall_call_id = webhook_data.get('id') or webhook_data.get('call_id')
        if not justcall_call_id:
            _logger.warning("JustCall webhook: Missing call ID")
            return None
        
        # Normalize phone numbers
        from_number = self._normalize_phone(webhook_data.get('from_number') or webhook_data.get('from'))
        to_number = self._normalize_phone(webhook_data.get('to_number') or webhook_data.get('to'))
        
        # Determine direction
        direction = 'inbound' if webhook_data.get('direction') == '1' else 'outbound'
        if webhook_data.get('type') == '1':
            direction = 'inbound'
        elif webhook_data.get('type') == '2':
            direction = 'outbound'
        
        # Determine contact number
        contact_number = from_number if direction == 'inbound' else to_number
        
        # Find or create call record
        call = self.search([('justcall_call_id', '=', str(justcall_call_id))], limit=1)
        
        # Parse call date
        call_date = fields.Datetime.now()
        if webhook_data.get('call_date') or webhook_data.get('created_at'):
            try:
                from datetime import datetime
                date_str = webhook_data.get('call_date') or webhook_data.get('created_at')
                # Try common formats
                for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S.%f']:
                    try:
                        call_date = datetime.strptime(date_str, fmt)
                        break
                    except:
                        continue
            except:
                pass
        
        # Map JustCall user to Odoo user
        user_id = False
        justcall_user_email = webhook_data.get('user_email') or webhook_data.get('email')
        if justcall_user_email:
            user = self.env['res.users'].search([('email', '=', justcall_user_email)], limit=1)
            if user:
                user_id = user.id
            else:
                # Try user mapping
                mapping = self.env['justcall.user.mapping'].search([
                    ('justcall_email', '=', justcall_user_email)
                ], limit=1)
                if mapping:
                    user_id = mapping.odoo_user_id.id
        
        # Match to partner/lead/project
        partner_id = False
        lead_id = False
        project_id = False
        if contact_number:
            # Try to match partner first
            partner = self.env['res.partner'].search([
                '|',
                ('phone', '=', contact_number),
                ('mobile', '=', contact_number),
            ], limit=1)
            if partner:
                partner_id = partner.id
                # Try to find project linked to this partner (most recent active project)
                project = self.env['project.project'].search([
                    ('partner_id', '=', partner_id),
                    ('active', '=', True),
                ], limit=1, order='create_date desc')
                if project:
                    project_id = project.id
            
            # Also try to match lead (in case partner wasn't found)
            if not partner_id:
                lead = self.env['crm.lead'].search([
                    '|',
                    ('phone', '=', contact_number),
                    ('mobile', '=', contact_number),
                ], limit=1)
                if lead:
                    lead_id = lead.id
                    # Try to find project linked to this lead
                    # Check if project model has ptt_crm_lead_id field
                    if 'ptt_crm_lead_id' in self.env['project.project']._fields:
                        project = self.env['project.project'].search([
                            ('ptt_crm_lead_id', '=', lead_id),
                            ('active', '=', True),
                        ], limit=1, order='create_date desc')
                        if project:
                            project_id = project.id
                            # Also set partner_id if project has a partner
                            if project.partner_id:
                                partner_id = project.partner_id.id
        
        # Prepare values
        values = {
            'justcall_call_id': str(justcall_call_id),
            'justcall_user_id': webhook_data.get('user_id'),
            'justcall_user_email': justcall_user_email,
            'call_date': call_date,
            'direction': direction,
            'status': self._map_status(webhook_data.get('status') or webhook_data.get('call_status')),
            'duration': webhook_data.get('duration') or webhook_data.get('call_duration') or 0,
            'from_number': from_number,
            'to_number': to_number,
            'contact_number': contact_number,
            'partner_id': partner_id,
            'lead_id': lead_id,
            'project_id': project_id,
            'user_id': user_id,
            'recording_url': webhook_data.get('recording_url') or webhook_data.get('recording'),
            'recording_duration': webhook_data.get('recording_duration'),
            'notes': webhook_data.get('notes') or webhook_data.get('disposition'),
            'transcription': webhook_data.get('transcription'),
            'cost': webhook_data.get('cost'),
            'tags': webhook_data.get('tags'),
            'raw_data': str(webhook_data),
        }
        
        if call:
            call.write(values)
        else:
            call = self.create(values)
        
        return call

    def _normalize_phone(self, phone):
        """Normalize phone number to E.164 format"""
        if not phone:
            return ""
        
        # Remove all non-digit characters except +
        import re
        normalized = re.sub(r'[^\d+]', '', str(phone))
        
        # Add + if missing and number starts with 1 (US)
        if normalized and not normalized.startswith('+'):
            if normalized.startswith('1') and len(normalized) == 11:
                normalized = '+' + normalized
            elif len(normalized) == 10:
                normalized = '+1' + normalized
        
        return normalized

    def _map_status(self, status):
        """Map JustCall status to Odoo status"""
        status_map = {
            '1': 'completed',
            '2': 'completed',
            '3': 'no-answer',
            '4': 'busy',
            '5': 'failed',
            '6': 'cancelled',
            'completed': 'completed',
            'no-answer': 'no-answer',
            'busy': 'busy',
            'failed': 'failed',
            'cancelled': 'cancelled',
        }
        return status_map.get(str(status), 'completed')
