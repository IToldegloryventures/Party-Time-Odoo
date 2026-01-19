# -*- coding: utf-8 -*-
from odoo import models, fields, _

from odoo.addons.ptt_business_core.constants import SERVICE_TYPES


class ResPartner(models.Model):
    """Partner extensions for Party Time Texas.
    
    Vendor identification uses native Odoo fields:
    - supplier_rank > 0 indicates a vendor
    - customer_rank > 0 indicates a customer
    """
    _inherit = "res.partner"

    # Vendor Classification (see supplier_rank for vendor toggle)
    ptt_vendor_service_types = fields.Many2many(
        "ptt.vendor.service.type",
        string="Service Types",
        help="Types of services this vendor provides.",
    )
    ptt_vendor_rating = fields.Selection(
        [
            ("1", "1 - Poor"),
            ("2", "2 - Fair"),
            ("3", "3 - Good"),
            ("4", "4 - Very Good"),
            ("5", "5 - Excellent"),
        ],
        string="Vendor Rating",
    )
    ptt_vendor_notes = fields.Text(
        string="Vendor Notes",
        help="Internal notes about this vendor.",
    )
    
    # Client Classification (see customer_rank for client toggle)
    ptt_client_type = fields.Selection(
        [
            ("individual", "Individual"),
            ("business", "Business"),
            ("nonprofit", "Non-Profit"),
            ("government", "Government"),
        ],
        string="Client Type",
    )

    ptt_opportunity_count = fields.Integer(
        string="PTT Opportunities",
        compute="_compute_ptt_opportunity_count",
    )
    
    # Preferred contact method
    ptt_preferred_contact = fields.Selection(
        [
            ("call", "Phone Call"),
            ("text", "Text Message"),
            ("email", "Email"),
        ],
        string="Preferred Contact Method",
    )

    def _compute_ptt_opportunity_count(self):
        """Count related opportunities for client contacts."""
        lead_model = self.env["crm.lead"]
        for partner in self:
            if partner.customer_rank <= 0:
                partner.ptt_opportunity_count = 0
                continue
            partner.ptt_opportunity_count = lead_model.search_count([
                ("partner_id", "child_of", partner.id),
                ("type", "=", "opportunity"),
            ])

    def action_view_ptt_opportunities(self):
        """Open related opportunities for this contact."""
        self.ensure_one()
        action = self.env.ref("crm.crm_lead_action_pipeline").read()[0]
        action["domain"] = [
            ("partner_id", "child_of", self.id),
            ("type", "=", "opportunity"),
        ]
        action["context"] = {
            **self.env.context,
            "default_partner_id": self.id,
            "default_type": "opportunity",
        }
        action["name"] = _("Opportunities")
        return action


class PttVendorServiceType(models.Model):
    """Vendor service type tags."""
    _name = "ptt.vendor.service.type"
    _description = "Vendor Service Type"
    _order = "sequence, name"

    name = fields.Char(string="Service Type", required=True)
    code = fields.Char(string="Code")
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    color = fields.Integer(string="Color Index")


