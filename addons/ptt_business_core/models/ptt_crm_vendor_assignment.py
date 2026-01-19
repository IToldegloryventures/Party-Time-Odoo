# -*- coding: utf-8 -*-
# Part of Party Time Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields

from odoo.addons.ptt_business_core.constants import SERVICE_TYPES


class PttCrmVendorAssignment(models.Model):
    """Vendor assignments at CRM Lead level.
    
    Similar to ptt.project.vendor.assignment but for early-stage vendor planning
    before a project is created. These can be transferred to project level later.
    """
    _name = "ptt.crm.vendor.assignment"
    _description = "CRM Lead Vendor Assignment"
    _order = "id"

    lead_id = fields.Many2one(
        "crm.lead",
        string="Lead/Opportunity",
        required=True,
        ondelete="cascade",
        index=True,
    )
    
    # Link to service line (optional)
    service_line_id = fields.Many2one(
        "ptt.crm.service.line",
        string="Service Line",
        domain="[('lead_id', '=', lead_id)]",
        ondelete="set null",
        help="Link to specific service line if applicable",
    )
    
    # Uses shared constant to avoid duplication (DRY principle)
    service_type = fields.Selection(
        SERVICE_TYPES,
        string="Service Type",
        required=True,
    )
    
    vendor_id = fields.Many2one(
        "res.partner",
        string="Vendor",
        domain="[('supplier_rank', '>', 0)]",
        ondelete="set null",
        help="Vendor to provide this service. Only shows contacts marked as suppliers.",
    )
    
    # Cost Estimation
    estimated_cost = fields.Monetary(
        string="Estimated Cost",
        currency_field="currency_id",
        help="Estimated cost we will pay to this vendor",
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )
    
    notes = fields.Text(string="Notes")
    
    # Status Tracking
    status = fields.Selection(
        [
            ("tentative", "Tentative"),
            ("requested", "Quote Requested"),
            ("quoted", "Quote Received"),
            ("confirmed", "Confirmed"),
            ("declined", "Declined"),
        ],
        string="Status",
        default="tentative",
        help="Track the status of this vendor assignment",
    )
    
    # Contact Info (for quick reference)
    vendor_contact_name = fields.Char(
        string="Vendor Contact",
        help="Primary contact person at the vendor",
    )
    vendor_contact_phone = fields.Char(
        string="Vendor Phone",
        related="vendor_id.phone",
        readonly=True,
    )
    vendor_contact_email = fields.Char(
        string="Vendor Email",
        related="vendor_id.email",
        readonly=True,
    )
