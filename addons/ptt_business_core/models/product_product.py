# Part of Party Time Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ProductProduct(models.Model):
    """
    Extends product.product (variants) with Party Time-specific pricing
    and service configuration fields.
    
    These fields are set PER VARIANT, not on the template.
    When a product has Event Type × Service Tier attributes with create_variant="always",
    9 variants are auto-created. Each variant can have different:
    - Minimum hours required
    - Guest count ranges
    - Pricing guides for sales reps
    - Vendor cost guides
    - Package inclusions
    """
    _inherit = 'product.product'

    # =====================================================
    # MINIMUM HOURS - Per Variant
    # Used for validation when adding to sale.order.line
    # =====================================================
    ptt_min_hours = fields.Float(
        string="Minimum Hours",
        help="Minimum number of hours required for this service variant. "
             "Sales order line quantity will be validated against this value.",
        default=0.0,
    )

    # =====================================================
    # GUEST COUNT RANGE - Per Variant
    # For reference on quotes - not enforced
    # =====================================================
    ptt_guest_count_min = fields.Integer(
        string="Min Guest Count",
        help="Recommended minimum guest count for this service tier.",
        default=0,
    )
    ptt_guest_count_max = fields.Integer(
        string="Max Guest Count",
        help="Recommended maximum guest count for this service tier.",
        default=0,
    )

    # =====================================================
    # PRICING GUIDE - For Sales Reps (Internal Only)
    # Shows on Pricing Reference tab in sale.order
    # =====================================================
    ptt_price_per_hour_min = fields.Float(
        string="Price/Hr (Min)",
        help="Minimum customer price per hour for this variant. "
             "Reference for sales reps - not enforced.",
        default=0.0,
    )
    ptt_price_per_hour_max = fields.Float(
        string="Price/Hr (Max)",
        help="Maximum customer price per hour for this variant. "
             "Reference for sales reps - not enforced.",
        default=0.0,
    )

    # =====================================================
    # VENDOR COST GUIDE - For Estimates (Internal Only)
    # Shows on Pricing Reference tab in sale.order
    # =====================================================
    ptt_cost_per_hour_min = fields.Float(
        string="Cost/Hr (Min)",
        help="Minimum vendor cost per hour for this variant. "
             "Used for margin calculations and vendor estimates.",
        default=0.0,
    )
    ptt_cost_per_hour_max = fields.Float(
        string="Cost/Hr (Max)",
        help="Maximum vendor cost per hour for this variant. "
             "Used for margin calculations and vendor estimates.",
        default=0.0,
    )

    # =====================================================
    # PACKAGE DESCRIPTION - What's Included
    # Shows on customer quotes for this variant
    # =====================================================
    ptt_package_includes = fields.Html(
        string="Package Includes",
        help="Description of what's included in this service tier. "
             "Displayed on customer quotations.",
        sanitize=True,
    )

    # =====================================================
    # TRANSITION PRICING - FY26 Promotional Rates
    # Special pricing for existing/early clients
    # =====================================================
    ptt_transition_price = fields.Float(
        string="Transition Starting Price",
        help="Special promotional starting price valid through FY26. "
             "Use this rate for existing clients or early bookings.",
        default=0.0,
    )
    ptt_transition_price_valid_until = fields.Date(
        string="Transition Price Valid Until",
        help="Date until which the transition price is valid.",
        default="2026-12-31",
    )

    # =====================================================
    # ADD-ONS - Suggested upsells for this variant
    # =====================================================
    ptt_addon_ids = fields.Many2many(
        'product.product',
        'ptt_product_addon_rel',
        'product_id',
        'addon_id',
        string="Suggested Add-ons",
        help="Products that can be offered as add-ons when this variant is selected.",
    )
