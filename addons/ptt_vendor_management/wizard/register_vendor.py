# Part of Party Time Texas Event Management System
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
"""
Vendor Registration Wizard.

Allows registering partners as vendors and creating portal access.
Inspired by Cybrosys Technologies vendor_portal_odoo module.
"""

from odoo import fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools import email_normalize


class RegisterVendor(models.TransientModel):
    """Wizard to register a partner as a vendor with portal access."""
    _name = "ptt.register.vendor"
    _description = "Register Vendor"

    partner_id = fields.Many2one(
        "res.partner",
        string="Partner",
        required=True,
        default=lambda self: self._default_partner_id(),
    )
    
    is_already_registered = fields.Boolean(
        string="Already Registered",
        compute="_compute_is_already_registered",
    )
    
    service_type_ids = fields.Many2many(
        "ptt.vendor.service.type",
        string="Service Types",
        help="Services this vendor provides",
    )
    
    create_portal_user = fields.Boolean(
        string="Create Portal User",
        default=True,
        help="Create a portal user account for this vendor",
    )
    
    send_invitation = fields.Boolean(
        string="Send Invitation Email",
        default=True,
        help="Send portal invitation email to vendor",
    )

    def _default_partner_id(self):
        """Get partner from context."""
        if self.env.context.get("active_model") == "res.partner":
            return self.env.context.get("active_id")
        return False

    def _compute_is_already_registered(self):
        """Check if partner is already a registered vendor."""
        for wizard in self:
            wizard.is_already_registered = bool(
                wizard.partner_id and wizard.partner_id.ptt_is_vendor
            )

    def action_register_vendor(self):
        """Register the partner as a vendor."""
        self.ensure_one()
        
        if not self.partner_id:
            raise ValidationError(_("Please select a partner."))
        
        if not self.partner_id.email:
            raise ValidationError(_("Partner must have an email address."))
        
        # Update partner as vendor
        vals = {
            "ptt_is_vendor": True,
        }
        if self.service_type_ids:
            vals["ptt_vendor_service_types"] = [(6, 0, self.service_type_ids.ids)]
        
        self.partner_id.write(vals)
        
        # Create portal user if requested
        if self.create_portal_user:
            self._create_portal_user()
        
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Vendor Registered"),
                "message": _("%s has been registered as a vendor.") % self.partner_id.name,
                "type": "success",
                "sticky": False,
            },
        }

    def _create_portal_user(self):
        """Create portal user for the vendor."""
        partner = self.partner_id
        
        # Check if user already exists
        existing_user = self.env["res.users"].sudo().search([
            ("partner_id", "=", partner.id)
        ], limit=1)
        
        if existing_user:
            # Ensure user has portal access
            portal_group = self.env.ref("base.group_portal", raise_if_not_found=False)
            if portal_group and portal_group not in existing_user.groups_id:
                existing_user.groups_id = [(4, portal_group.id)]
            return existing_user
        
        # Create new portal user
        user = self.env["res.users"].with_context(
            no_reset_password=not self.send_invitation
        ).sudo()._create_user_from_template({
            "email": email_normalize(partner.email),
            "login": email_normalize(partner.email),
            "partner_id": partner.id,
            "company_id": self.env.company.id,
            "company_ids": [(6, 0, self.env.company.ids)],
            "active": True,
        })
        
        if self.send_invitation:
            user.action_reset_password()
        
        return user

    def action_send_password_reset(self):
        """Send password reset email to existing user."""
        self.ensure_one()
        
        user = self.env["res.users"].sudo().search([
            ("partner_id", "=", self.partner_id.id)
        ], limit=1)
        
        if user:
            user.action_reset_password()
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Email Sent"),
                    "message": _("Password reset email sent to %s") % self.partner_id.email,
                    "type": "success",
                    "sticky": False,
                },
            }
        else:
            raise ValidationError(_("No user account found for this partner."))


class RfqSelectVendor(models.TransientModel):
    """Wizard to select winning vendor from RFQ quotes."""
    _name = "ptt.rfq.select.vendor"
    _description = "Select Vendor for RFQ"

    rfq_id = fields.Many2one(
        "ptt.vendor.rfq",
        string="RFQ",
        required=True,
    )
    quote_ids = fields.Many2many(
        "ptt.vendor.quote.history",
        string="Available Quotes",
    )
    selected_quote_id = fields.Many2one(
        "ptt.vendor.quote.history",
        string="Selected Quote",
        domain="[('id', 'in', quote_ids)]",
        required=True,
    )
    
    # Display fields
    vendor_name = fields.Char(
        related="selected_quote_id.vendor_id.name",
    )
    quoted_price = fields.Monetary(
        related="selected_quote_id.quoted_price",
    )
    currency_id = fields.Many2one(
        related="rfq_id.currency_id",
    )

    def action_select_vendor(self):
        """Approve the selected vendor."""
        self.ensure_one()
        self.rfq_id.action_approve_vendor(
            self.selected_quote_id.vendor_id.id,
            self.selected_quote_id.id,
        )
        return {"type": "ir.actions.act_window_close"}
