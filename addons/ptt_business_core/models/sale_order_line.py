from odoo import models, fields, api


class SaleOrderLine(models.Model):
    """Extend sale.order.line with variant pricing info for internal reference.
    
    These fields show sales reps the MIN/MAX pricing ranges and minimum hours
    for the selected DJ service variant. INTERNAL USE ONLY - never printed.
    
    Reference: https://www.odoo.com/documentation/19.0/developer/reference/backend/orm.html
    
    FIELD NAMING:
    - All custom fields use ptt_ prefix (Party Time Texas)
    """
    _inherit = "sale.order.line"

    # === VARIANT PRICING REFERENCE (Related fields) ===
    # These pull from the product variant's ptt_* fields for quick reference
    
    ptt_price_min = fields.Monetary(
        string="Min Rate",
        related="product_id.ptt_price_per_hour_min",
        readonly=True,
        help="Minimum hourly rate for this variant (floor for negotiations).",
    )
    ptt_price_max = fields.Monetary(
        string="Max Rate", 
        related="product_id.ptt_price_per_hour_max",
        readonly=True,
        help="Maximum hourly rate for this variant (ceiling for negotiations).",
    )
    ptt_min_hours = fields.Float(
        string="Min Hours",
        related="product_id.ptt_min_hours",
        readonly=True,
        help="Minimum hours required for this service variant.",
    )
    ptt_guest_count_min = fields.Integer(
        string="Guests (Min)",
        related="product_id.ptt_guest_count_min",
        readonly=True,
    )
    ptt_guest_count_max = fields.Integer(
        string="Guests (Max)",
        related="product_id.ptt_guest_count_max",
        readonly=True,
    )
    ptt_package_includes = fields.Html(
        string="What's Included",
        related="product_id.ptt_package_includes",
        readonly=True,
    )
    
    # === PRICING STATUS INDICATORS ===
    ptt_price_status = fields.Selection(
        [
            ('below_min', 'Below Minimum'),
            ('in_range', 'In Range'),
            ('above_max', 'Above Maximum'),
            ('no_range', 'No Range Set'),
        ],
        string="Price Status",
        compute="_compute_price_status",
        help="Indicates if unit price is within the allowed range.",
    )
    
    ptt_hours_status = fields.Selection(
        [
            ('below_min', 'Below Minimum'),
            ('meets_min', 'Meets Minimum'),
            ('no_min', 'No Minimum'),
        ],
        string="Hours Status",
        compute="_compute_hours_status",
        help="Indicates if quantity meets minimum hours requirement.",
    )

    @api.depends('price_unit', 'ptt_price_min', 'ptt_price_max')
    def _compute_price_status(self):
        """Check if unit price is within the allowed min/max range."""
        for line in self:
            if not line.ptt_price_min and not line.ptt_price_max:
                line.ptt_price_status = 'no_range'
            elif line.price_unit < line.ptt_price_min:
                line.ptt_price_status = 'below_min'
            elif line.ptt_price_max and line.price_unit > line.ptt_price_max:
                line.ptt_price_status = 'above_max'
            else:
                line.ptt_price_status = 'in_range'

    @api.depends('product_uom_qty', 'ptt_min_hours')
    def _compute_hours_status(self):
        """Check if quantity meets minimum hours requirement."""
        for line in self:
            if not line.ptt_min_hours:
                line.ptt_hours_status = 'no_min'
            elif line.product_uom_qty < line.ptt_min_hours:
                line.ptt_hours_status = 'below_min'
            else:
                line.ptt_hours_status = 'meets_min'

    @api.onchange('product_id', 'product_uom_qty')
    def _onchange_check_minimums(self):
        """Warn sales rep if hours are below minimum for this variant."""
        if self.ptt_min_hours and self.product_uom_qty < self.ptt_min_hours:
            return {
                'warning': {
                    'title': 'Below Minimum Hours',
                    'message': f'This service requires a minimum of {self.ptt_min_hours} hours. '
                               f'Current quantity: {self.product_uom_qty} hours.',
                }
            }

    @api.onchange('price_unit')
    def _onchange_check_price_range(self):
        """Warn sales rep if price is outside the allowed range."""
        if self.ptt_price_min and self.price_unit < self.ptt_price_min:
            return {
                'warning': {
                    'title': 'Price Below Minimum',
                    'message': f'Unit price ${self.price_unit:.2f} is below the minimum rate '
                               f'of ${self.ptt_price_min:.2f} for this service.',
                }
            }
        if self.ptt_price_max and self.price_unit > self.ptt_price_max:
            return {
                'warning': {
                    'title': 'Price Above Maximum', 
                    'message': f'Unit price ${self.price_unit:.2f} exceeds the maximum rate '
                               f'of ${self.ptt_price_max:.2f} for this service.',
                }
            }
