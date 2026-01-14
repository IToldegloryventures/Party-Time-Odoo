# -*- coding: utf-8 -*-

import base64
import logging
import requests
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class JustCallConfig(models.Model):
    _name = 'justcall.config'
    _description = 'JustCall Configuration'
    _order = 'create_date desc'

    name = fields.Char(
        string="Configuration Name",
        default="JustCall Configuration",
        required=True,
    )
    api_key = fields.Char(
        string="API Key",
        required=True,
        copy=False,
        help="Your JustCall API Key from Profile → APIs and Webhooks",
    )
    api_secret = fields.Char(
        string="API Secret",
        required=True,
        copy=False,
        help="Your JustCall API Secret from Profile → APIs and Webhooks",
    )
    webhook_secret = fields.Char(
        string="Webhook Secret",
        copy=False,
        help="Optional: Secret for webhook signature validation",
    )
    webhook_url = fields.Char(
        string="Webhook URL",
        compute='_compute_webhook_url',
        help="Configure this URL in JustCall webhook settings",
    )
    active = fields.Boolean(
        string="Active",
        default=True,
        help="Only one active configuration per company",
    )
    company_id = fields.Many2one(
        'res.company',
        string="Company",
        default=lambda self: self.env.company,
        required=True,
        ondelete='cascade',
    )
    connection_status = fields.Selection(
        [
            ('not_tested', 'Not Tested'),
            ('connected', 'Connected'),
            ('failed', 'Connection Failed'),
        ],
        string="Connection Status",
        default='not_tested',
        readonly=True,
    )
    last_test_date = fields.Datetime(
        string="Last Test Date",
        readonly=True,
    )
    test_message = fields.Text(
        string="Test Message",
        readonly=True,
    )
    call_count = fields.Integer(
        string="Call Count",
        compute='_compute_call_count',
    )

    def _compute_call_count(self):
        """Compute total call count"""
        for config in self:
            config.call_count = self.env['justcall.call'].search_count([])

    def action_view_calls(self):
        """Open call history"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'JustCall Calls',
            'res_model': 'justcall.call',
            'view_mode': 'tree,form',
            'domain': [],
        }

    _sql_constraints = [
        ('unique_active_company', 'unique(company_id, active)',
         'Only one active configuration is allowed per company!'),
    ]

    @api.depends('company_id')
    def _compute_webhook_url(self):
        """Compute webhook URL based on company's base URL"""
        for config in self:
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            if base_url:
                config.webhook_url = f"{base_url.rstrip('/')}/justcall/webhook"
            else:
                config.webhook_url = ""

    @api.constrains('active', 'company_id')
    def _check_active_config(self):
        """Ensure only one active configuration per company"""
        for config in self:
            if config.active:
                existing = self.search([
                    ('company_id', '=', config.company_id.id),
                    ('active', '=', True),
                    ('id', '!=', config.id),
                ])
                if existing:
                    raise ValidationError(
                        _("Only one active configuration is allowed per company. "
                          "Please deactivate the existing configuration first.")
                    )

    def _get_auth_headers(self):
        """Generate authentication headers for JustCall API"""
        if not self.api_key or not self.api_secret:
            raise UserError(_("API Key and API Secret are required"))
        
        # Basic Auth: base64(api_key:api_secret)
        credentials = f"{self.api_key}:{self.api_secret}"
        encoded = base64.b64encode(credentials.encode()).decode()
        
        return {
            'Authorization': f'Basic {encoded}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

    def test_connection(self):
        """Test connection to JustCall API"""
        self.ensure_one()
        
        try:
            headers = self._get_auth_headers()
            url = 'https://api.justcall.io/v2.1/users'
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.write({
                    'connection_status': 'connected',
                    'last_test_date': fields.Datetime.now(),
                    'test_message': _("Connection successful. Found %d users.") % len(data.get('data', [])),
                })
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Success'),
                        'message': _('Connection to JustCall API successful!'),
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                error_msg = response.text or _("Unknown error")
                self.write({
                    'connection_status': 'failed',
                    'last_test_date': fields.Datetime.now(),
                    'test_message': _("Connection failed: %s (Status: %s)") % (error_msg, response.status_code),
                })
                raise UserError(_("Connection failed: %s") % error_msg)
                
        except requests.exceptions.RequestException as e:
            self.write({
                'connection_status': 'failed',
                'last_test_date': fields.Datetime.now(),
                'test_message': _("Connection error: %s") % str(e),
            })
            raise UserError(_("Connection error: %s") % str(e))
        except Exception as e:
            _logger.error("JustCall connection test error: %s", str(e))
            self.write({
                'connection_status': 'failed',
                'last_test_date': fields.Datetime.now(),
                'test_message': _("Error: %s") % str(e),
            })
            raise UserError(_("Error testing connection: %s") % str(e))

    @api.model
    def get_active_config(self, company_id=None):
        """Get active configuration for company"""
        if company_id is None:
            company_id = self.env.company.id
        
        config = self.sudo().search([
            ('company_id', '=', company_id),
            ('active', '=', True),
        ], limit=1)
        
        if not config:
            raise UserError(_("No active JustCall configuration found. Please configure in Settings → JustCall Configuration."))
        
        return config
