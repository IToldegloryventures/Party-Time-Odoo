# -*- coding: utf-8 -*-
# Part of Party Time Texas Event Management System
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
"""
CRM Service Line Model

This model captures structured service selections within CRM opportunities
BEFORE creating a sale order. It lets sales reps build multi-tier service
packages during the lead/opportunity stage.

Unlike sale.order.line which is created after quoting, ptt.crm.service.line
captures the initial service requirements during discovery/proposal phases.
"""

from odoo import models, fields, api

from odoo.addons.ptt_business_core.constants import SERVICE_TYPES, SERVICE_TIERS


class PttCrmServiceLine(models.Model):
    """Service line for CRM opportunities - structured service selection."""
    _name = "ptt.crm.service.line"
    _description = "CRM Service Line"
    _order = "sequence, id"

    # Constraints (Odoo 19 style)
    _positive_hours = models.Constraint(
        'CHECK(hours >= 0)',
        'Hours cannot be negative.',
    )
    _positive_quantity = models.Constraint(
        'CHECK(quantity >= 0)',
        'Quantity cannot be negative.',
    )

    # =========================================================================
    # RELATIONSHIPS
    # =========================================================================
    crm_lead_id = fields.Many2one(
        "crm.lead",
        string="Opportunity",
        required=True,
        ondelete="cascade",
        index=True,
    )
    product_id = fields.Many2one(
        "product.product",
        string="Service Product",
        domain="[('sale_ok', '=', True)]",
        help="Link to product catalog for pricing. Leave empty for custom services.",
    )

    # =========================================================================
    # SERVICE DETAILS
    # =========================================================================
    sequence = fields.Integer(
        string="Sequence",
        default=10,
    )
    service_type = fields.Selection(
        selection=SERVICE_TYPES,
        string="Service Type",
        required=True,
    )
    service_tier = fields.Selection(
        selection=SERVICE_TIERS,
        string="Service Tier",
        required=True,
        help="Essential = Basic package, Classic = Standard, Premier = Premium",
    )
    name = fields.Char(
        string="Description",
        compute="_compute_name",
        store=True,
        readonly=False,
        help="Service description - auto-generated from product or service type",
    )

    # =========================================================================
    # QUANTITY & PRICING
    # =========================================================================
    quantity = fields.Float(
        string="Quantity",
        default=1.0,
        required=True,
    )
    hours = fields.Float(
        string="Hours",
        default=4.0,
        help="Estimated service hours",
    )
    unit_price = fields.Monetary(
        string="Unit Price",
        currency_field="currency_id",
        compute="_compute_unit_price",
        store=True,
        readonly=False,
        help="Price per unit/hour. Auto-filled from product if linked.",
    )
    subtotal = fields.Monetary(
        string="Subtotal",
        currency_field="currency_id",
        compute="_compute_subtotal",
        store=True,
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        related="crm_lead_id.company_currency",
        store=True,
        readonly=True,
    )

    # =========================================================================
    # RELATED FIELDS FROM PRODUCT (for display)
    # =========================================================================
    product_min_hours = fields.Float(
        string="Min Hours",
        related="product_id.ptt_min_hours",
        readonly=True,
    )
    product_includes = fields.Html(
        string="Package Includes",
        related="product_id.ptt_package_includes",
        readonly=True,
    )

    # =========================================================================
    # NOTES
    # =========================================================================
    notes = fields.Text(
        string="Notes",
        help="Special requirements or notes for this service",
    )

    # =========================================================================
    # COMPUTED METHODS
    # =========================================================================
    @api.depends('product_id', 'service_type', 'service_tier')
    def _compute_name(self):
        """Generate description from service type + tier, not product name."""
        tier_labels = dict(SERVICE_TIERS)
        type_labels = dict(SERVICE_TYPES)
        for line in self:
            # ALWAYS prioritize service_type + tier for display
            if line.service_type and line.service_tier:
                type_name = type_labels.get(line.service_type, line.service_type)
                tier_name = tier_labels.get(line.service_tier, line.service_tier)
                line.name = f"{type_name} - {tier_name}"
            elif line.service_type:
                type_name = type_labels.get(line.service_type, line.service_type)
                line.name = type_name
            elif line.product_id:
                line.name = line.product_id.display_name
            else:
                line.name = "New Service"

    @api.depends('product_id', 'service_tier')
    def _compute_unit_price(self):
        """Get unit price from product or default to 0."""
        for line in self:
            if line.product_id:
                # Use the product's list price
                line.unit_price = line.product_id.lst_price
            elif not line.unit_price:
                line.unit_price = 0.0

    @api.depends('quantity', 'hours', 'unit_price')
    def _compute_subtotal(self):
        """Calculate subtotal using quantity and hours when provided."""
        for line in self:
            if line.hours and line.hours > 0:
                line.subtotal = line.unit_price * line.hours * line.quantity
            else:
                line.subtotal = line.unit_price * line.quantity

    # =========================================================================
    # ONCHANGE METHODS
    # =========================================================================
    @api.onchange('product_id')
    def _onchange_product_id(self):
        """When product is selected, populate service type and tier from variant."""
        if self.product_id:
            # Try to extract tier from variant attributes
            for attr_val in self.product_id.product_template_attribute_value_ids:
                attr_name = attr_val.attribute_id.name.lower()
                val_name = attr_val.product_attribute_value_id.name.lower()
                
                # Map attribute values to our tier selections
                if 'tier' in attr_name:
                    if 'essential' in val_name:
                        self.service_tier = 'essentials'
                    elif 'classic' in val_name:
                        self.service_tier = 'classic'
                    elif 'premier' in val_name:
                        self.service_tier = 'premier'
            
            # Get min hours from product
            if self.product_id.ptt_min_hours and self.hours < self.product_id.ptt_min_hours:
                self.hours = self.product_id.ptt_min_hours

    @api.onchange('hours', 'product_id')
    def _onchange_hours_warning(self):
        """Warn if hours are below minimum."""
        if self.product_id and self.product_id.ptt_min_hours:
            if self.hours < self.product_id.ptt_min_hours:
                return {
                    'warning': {
                        'title': "Below Minimum Hours",
                        'message': f"This service tier requires at least "
                                   f"{self.product_id.ptt_min_hours} hours. "
                                   f"You entered {self.hours} hours.",
                    }
                }
