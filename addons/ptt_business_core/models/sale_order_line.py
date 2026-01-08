from odoo import models, fields, api


class SaleOrderLine(models.Model):
    """Extend Sale Order Line with Target Margin field for reference pricing.
    
    Sales reps can enter a Target Margin percentage to see what the recommended
    Unit Price should be based on the product's cost. This is for REFERENCE ONLY
    and does NOT automatically update the Unit Price (to preserve finance team's setup).
    
    Formula: Recommended Price = Purchase Price / (1 - Target Margin)
    Example: If cost is $100 and target margin is 50% (0.50), recommended price = 100 / (1 - 0.50) = $200
    """
    _inherit = "sale.order.line"

    # === TARGET MARGIN FIELD ===
    x_target_margin = fields.Float(
        string="Target Margin",
        digits=(16, 4),
        help="Target margin percentage. Enter as decimal (50% = 0.50). "
             "This is for reference - see 'Target Margin Price' below for recommended price.",
    )
    
    # === TARGET MARGIN PRICE (READ-ONLY REFERENCE) ===
    x_target_margin_price = fields.Monetary(
        string="Target Margin Price",
        compute="_compute_target_margin_price",
        currency_field="currency_id",
        readonly=True,
        store=False,
        help="Recommended Unit Price based on Target Margin and Cost. "
             "This is for REFERENCE ONLY - Unit Price is not automatically updated.",
    )

    @api.onchange('x_target_margin', 'purchase_price', 'product_id')
    def _onchange_target_margin(self):
        """Trigger recalculation when target margin or cost changes."""
        # Trigger the compute method
        self._compute_target_margin_price()

    @api.depends('x_target_margin', 'purchase_price', 'product_id', 'currency_id', 'product_uom_id', 'company_id')
    def _compute_target_margin_price(self):
        """Calculate recommended price based on Target Margin and Cost.
        
        Formula: Recommended Price = Purchase Price / (1 - Target Margin)
        This is READ-ONLY and for reference only - does NOT update price_unit.
        """
        for line in self:
            # Skip if missing required data
            if not line.product_id:
                line.x_target_margin_price = 0.0
                continue
            
            # Get purchase price (cost) - from sale_margin module
            # purchase_price is a computed field with precompute=True, so it should be available
            # It's computed based on: product_id, company_id, currency_id, product_uom_id
            # Access purchase_price - it may require base.group_user permission
            # If purchase_price is not available, try to get standard_price directly
            if hasattr(line, 'purchase_price'):
                cost = line.purchase_price or 0.0
            else:
                # Fallback: get cost directly from product if purchase_price not available
                if line.product_id:
                    # Convert product standard_price to line currency and UoM
                    product_cost = line.product_id.uom_id._compute_price(
                        line.product_id.standard_price,
                        line.product_uom_id,
                    )
                    cost = line._convert_to_sol_currency(
                        product_cost,
                        line.product_id.cost_currency_id
                    ) if hasattr(line, '_convert_to_sol_currency') else product_cost
                else:
                    cost = 0.0
            
            target_margin = line.x_target_margin or 0.0
            
            # Only calculate if both cost and margin are provided
            # Note: target_margin is stored as decimal (0.30 = 30%) due to percentage widget
            # Percentage widget stores: 30% input = 0.30 in database, displays as "30%"
            if cost > 0 and target_margin > 0 and target_margin < 1:
                # Formula: Price = Cost / (1 - Margin)
                # Example: $100 cost, 50% margin (0.50) = 100 / (1 - 0.50) = 100 / 0.50 = $200
                # Example: $100 cost, 30% margin (0.30) = 100 / (1 - 0.30) = 100 / 0.70 = $142.86
                try:
                    line.x_target_margin_price = cost / (1 - target_margin)
                except ZeroDivisionError:
                    line.x_target_margin_price = 0.0
            else:
                line.x_target_margin_price = 0.0
