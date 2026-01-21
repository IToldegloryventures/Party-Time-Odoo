# -*- coding: utf-8 -*-
"""
PTT Vendor Service Pricing Model

Tracks what each vendor charges for their services.
Allows sales team to quickly compare vendor rates when assigning to events.
"""
from odoo import models, fields, api


class PttVendorServicePricing(models.Model):
    """Service pricing per vendor.
    
    Each vendor can have multiple services with their rates.
    Used for quick price comparison when selecting vendors.
    """
    _name = "ptt.vendor.service.pricing"
    _description = "Vendor Service Pricing"
    _order = "service_type_id"
    _rec_name = "display_name"

    vendor_id = fields.Many2one(
        "res.partner",
        string="Vendor",
        required=True,
        ondelete="cascade",
        index=True,
        domain="[('supplier_rank', '>', 0)]",
    )
    
    service_type_id = fields.Many2one(
        "ptt.vendor.service.type",
        string="Service Type",
        required=True,
        index=True,
        help="The service this vendor provides",
    )
    
    price_detail = fields.Char(
        string="Price/Rate",
        help="Price or rate for this service (e.g., '$150/hr', '$500 flat', 'Varies')",
    )
    
    notes = fields.Text(
        string="Notes",
        help="Additional notes about pricing (minimums, packages, discounts, etc.)",
    )
    
    display_name = fields.Char(
        string="Display Name",
        compute="_compute_display_name",
        store=True,
    )
    
    @api.depends("vendor_id.name", "service_type_id.name")
    def _compute_display_name(self):
        for record in self:
            vendor = record.vendor_id.name or "?"
            service = record.service_type_id.name or "?"
            record.display_name = f"{vendor} - {service}"

    _sql_constraints = [
        ('unique_vendor_service_type', 'UNIQUE(vendor_id, service_type_id)', 'Each vendor can only have one pricing entry per service type.'),
    ]
