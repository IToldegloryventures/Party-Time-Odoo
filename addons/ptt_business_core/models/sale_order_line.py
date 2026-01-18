# Part of Party Time Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleOrderLine(models.Model):
    """
    Extends sale.order.line with minimum hours validation and tier-related fields.
    
    When a product variant has ptt_min_hours > 0 and the line quantity
    is less than that minimum, a warning is shown to the user.
    """
    _inherit = 'sale.order.line'

    # =========================================================================
    # RELATED FIELDS FROM PRODUCT VARIANT - For Display in Views
    # =========================================================================
    ptt_min_hours = fields.Float(
        string="Min Hours",
        related='product_id.ptt_min_hours',
        readonly=True,
        help="Minimum hours required for this service tier.",
    )
    ptt_price_per_hour_min = fields.Float(
        string="Price/Hr (Low)",
        related='product_id.ptt_price_per_hour_min',
        readonly=True,
    )
    ptt_price_per_hour_max = fields.Float(
        string="Price/Hr (High)",
        related='product_id.ptt_price_per_hour_max',
        readonly=True,
    )
    ptt_cost_per_hour_min = fields.Float(
        string="Cost/Hr (Low)",
        related='product_id.ptt_cost_per_hour_min',
        readonly=True,
    )
    ptt_cost_per_hour_max = fields.Float(
        string="Cost/Hr (High)",
        related='product_id.ptt_cost_per_hour_max',
        readonly=True,
    )
    ptt_guest_count_min = fields.Integer(
        string="Guests (Min)",
        related='product_id.ptt_guest_count_min',
        readonly=True,
    )
    ptt_guest_count_max = fields.Integer(
        string="Guests (Max)",
        related='product_id.ptt_guest_count_max',
        readonly=True,
    )
    ptt_package_includes = fields.Html(
        string="Package Includes",
        related='product_id.ptt_package_includes',
        readonly=True,
    )

    # =========================================================================
    # COMPUTED FIELDS
    # =========================================================================
    ptt_min_hours_warning = fields.Char(
        string="Min Hours Warning",
        compute='_compute_ptt_min_hours_warning',
        store=False,
        help="Warning message when quantity is below minimum hours.",
    )

    @api.depends('product_id', 'product_uom_qty')
    def _compute_ptt_min_hours_warning(self):
        """Compute warning if quantity is below minimum hours for the variant."""
        for line in self:
            warning = ""
            if line.product_id and line.product_id.ptt_min_hours:
                min_hours = line.product_id.ptt_min_hours
                if line.product_uom_qty < min_hours:
                    warning = _(
                        "Below Minimum Hours: This service tier requires at least "
                        "%(min_hours)s hours. Current quantity: %(qty)s hours.",
                        min_hours=min_hours,
                        qty=line.product_uom_qty
                    )
            line.ptt_min_hours_warning = warning

    @api.onchange('product_id', 'product_uom_qty')
    def _onchange_ptt_min_hours_validation(self):
        """
        Show warning dialog when quantity is below minimum hours.
        
        This triggers the Odoo native warning dialog - user can still proceed
        but they're informed of the minimum requirement.
        """
        if self.product_id and self.product_id.ptt_min_hours:
            min_hours = self.product_id.ptt_min_hours
            if self.product_uom_qty and self.product_uom_qty < min_hours:
                return {
                    'warning': {
                        'title': _("Below Minimum Hours"),
                        'message': _(
                            "The service '%(product)s' requires a minimum of "
                            "%(min_hours)s hours for this tier.\n\n"
                            "You've entered %(qty)s hour(s). Please confirm "
                            "this is intentional or adjust the quantity.",
                            product=self.product_id.display_name,
                            min_hours=min_hours,
                            qty=self.product_uom_qty
                        ),
                    }
                }
        return {}
