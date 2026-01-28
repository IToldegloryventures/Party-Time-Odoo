# -*- coding: utf-8 -*-
"""
Vendor Invite Wizard

This wizard allows users to send email invitations to potential vendors,
inviting them to apply through the vendor application portal.

Reference: https://www.odoo.com/documentation/19.0/developer/tutorials/server_framework_101/07_onchange.html
"""
import logging
import re

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class PTTVendorInviteWizard(models.TransientModel):
    """Wizard to send vendor application invitations."""
    
    _name = "ptt.vendor.invite.wizard"
    _description = "Vendor Invite Wizard"
    
    # === RECIPIENT FIELDS ===
    recipient_name = fields.Char(
        string="Recipient Name",
        required=True,
        help="Name of the person/company to invite",
    )
    
    recipient_email = fields.Char(
        string="Recipient Email",
        required=True,
        help="Email address to send the invitation to",
    )
    
    recipient_phone = fields.Char(
        string="Phone (Optional)",
        help="Phone number of the potential vendor",
    )
    
    # === COMPUTED URLS ===
    website_url = fields.Char(
        string="Website URL",
        compute="_compute_template_vars",
        store=False,
    )
    
    application_url = fields.Char(
        string="Application URL",
        compute="_compute_template_vars",
        store=False,
    )
    
    # === SERVICE SUGGESTION ===
    suggested_service_ids = fields.Many2many(
        "ptt.vendor.service.type",
        string="Suggested Services",
        help="Service types you want this vendor to consider applying for",
    )
    
    # === PERSONAL MESSAGE ===
    personal_message = fields.Text(
        string="Personal Message",
        help="Optional personal message to include in the invitation email",
    )
    
    @api.depends("recipient_email", "recipient_name")
    def _compute_template_vars(self):
        """Compute website and application URLs."""
        for record in self:
            website_url = self.env["ir.config_parameter"].sudo().get_param(
                "web.base.url", ""
            )
            if not website_url:
                website_url = "http://localhost:8069"
            
            record.website_url = website_url
            record.application_url = f"{website_url}/vendor/apply"
    
    @api.constrains("recipient_email")
    def _check_email_format(self):
        """Validate email format."""
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        for record in self:
            if record.recipient_email and not re.match(email_pattern, record.recipient_email):
                raise ValidationError(_("Please enter a valid email address."))
    
    def action_send_invite(self):
        """Send invitation email to the potential vendor."""
        self.ensure_one()
        
        if not self.recipient_name or not self.recipient_email:
            raise UserError(_("Please provide name and email for the recipient."))
        
        # Check if a partner already exists with this email
        existing_partner = self.env["res.partner"].search([
            ("email", "=", self.recipient_email)
        ], limit=1)
        
        if existing_partner and existing_partner.supplier_rank > 0:
            raise UserError(
                _("A vendor already exists with this email address: %s") % existing_partner.name
            )
        
        # Check if user already exists
        existing_user = self.env["res.users"].sudo().search([
            ("login", "=", self.recipient_email)
        ], limit=1)
        
        # Create partner if doesn't exist
        if not existing_partner:
            partner = self.env["res.partner"].create({
                "name": self.recipient_name,
                "email": self.recipient_email,
                "phone": self.recipient_phone or False,
                "is_company": True,
                "supplier_rank": 0,  # Not a vendor YET - they need to apply
                "ptt_vendor_status": "new",
            })
        else:
            partner = existing_partner
        
        # Create portal user if doesn't exist
        if not existing_user:
            portal_group = self.env.ref("base.group_portal")
            user = self.env["res.users"].sudo().with_context(no_reset_password=True).create({
                "name": self.recipient_name,
                "login": self.recipient_email,
                "email": self.recipient_email,
                "partner_id": partner.id,
                "groups_id": [(6, 0, [portal_group.id])],
                "active": True,
                "company_id": self.env.company.id,
            })
            _logger.info("Created portal user for vendor invite: %s", self.recipient_email)
        else:
            user = existing_user
        
        # Send the invitation email
        self._send_invitation_email(partner, user)
        
        # Log note on the partner
        partner.message_post(
            body=_("Vendor application invitation sent by %s") % self.env.user.name,
            message_type="notification",
        )
        
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Success"),
                "message": _("Invitation email sent to %s") % self.recipient_email,
                "type": "success",
                "sticky": False,
                "next": {"type": "ir.actions.act_window_close"},
            }
        }
    
    def _send_invitation_email(self, partner, user):
        """Send the vendor invite email using mail template."""
        template = self.env.ref(
            "ptt_vendor_management.email_template_vendor_invite",
            raise_if_not_found=False
        )
        
        if template:
            # Build context with custom values
            ctx = {
                "recipient_name": self.recipient_name,
                "application_url": self.application_url,
                "personal_message": self.personal_message or "",
                "suggested_services": ", ".join(self.suggested_service_ids.mapped("name")) if self.suggested_service_ids else "",
                "sender_name": self.env.user.name,
                "company_name": self.env.company.name,
            }
            
            try:
                template.with_context(**ctx).send_mail(
                    self.id,
                    force_send=True,
                    email_values={
                        "email_to": self.recipient_email,
                    }
                )
                _logger.info("Vendor invitation email sent to: %s", self.recipient_email)
            except Exception as e:
                _logger.error("Error sending vendor invite to %s: %s", self.recipient_email, str(e))
                raise UserError(_("Failed to send invitation email: %s") % str(e))
        else:
            # Fallback: Send portal welcome email
            portal_template = self.env.ref("portal.mail_template_data_portal_welcome", raise_if_not_found=False)
            if portal_template:
                portal_template.sudo().send_mail(user.id, force_send=True)
                _logger.info("Sent portal welcome email as fallback for vendor invite: %s", self.recipient_email)
    
    def action_send_multiple(self):
        """Placeholder for sending to multiple recipients from a list."""
        # Future enhancement: Import from CSV or select from contacts
        raise UserError(_("Bulk invitations not yet implemented. Please send individually."))
