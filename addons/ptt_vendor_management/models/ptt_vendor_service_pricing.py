# -*- coding: utf-8 -*-
"""
PTT Vendor Service Pricing Model

Tracks what each vendor charges for their services.
Allows sales team to quickly compare vendor rates when assigning to events.

Links directly to product.template (service products) for automatic sync
with Sales > Products > Services.
"""
from odoo import models, fields, api


class PttVendorServicePricing(models.Model):
    """Service pricing per vendor.
    
    Each vendor can have multiple services with their rates.
    Used for quick price comparison when selecting vendors.
    Links directly to actual Odoo service products.
    """
    _name = "ptt.vendor.service.pricing"
    _description = "Vendor Service Pricing"
    _order = "service_product_id"
    _rec_name = "name"

    # Stored name field for _rec_name (Odoo 19 best practice)
    # Using stored field avoids performance issues in large lists
    name = fields.Char(
        string="Name",
        compute="_compute_name",
        store=True,
        index=True,
    )

    vendor_id = fields.Many2one(
        "res.partner",
        string="Vendor",
        required=True,
        ondelete="cascade",
        index=True,
        domain="[('supplier_rank', '>', 0)]",
    )
    
    service_product_id = fields.Many2one(
        "product.template",
        string="Service",
        required=True,
        index=True,
        domain="[('type', '=', 'service'), ('sale_ok', '=', True)]",
        help="The service product this vendor provides. Select from Sales > Products.",
    )
    
    price_detail = fields.Char(
        string="Price/Rate",
        help="Price or rate for this service (e.g., '$150/hr', '$500 flat', 'Varies')",
    )
    
    notes = fields.Text(
        string="Notes",
        help="Additional notes about pricing (minimums, packages, discounts, etc.)",
    )
    
    # =========================================================================
    # SQL CONSTRAINTS
    # =========================================================================
    _unique_vendor_service_product = models.Constraint(
        'UNIQUE (vendor_id, service_product_id)',
        'Each vendor can only have one pricing entry per service.',
    )

    @api.depends("vendor_id.name", "service_product_id.name")
    def _compute_name(self):
        """Compute stored name field for efficient list display."""
        for record in self:
            vendor = record.vendor_id.name or "?"
            service = record.service_product_id.name or "?"
            record.name = f"{vendor} - {service}"
