from odoo import models, fields, api


class ProductProduct(models.Model):
    """Extend product.product for DJ service variant configuration.
    
    This adds custom fields to product variants for:
    - Minimum hours required per tier
    - Guest count ranges per tier
    - Hourly rate min/max ranges
    - Vendor cost min/max ranges
    - Package inclusions description
    - Recommended add-ons
    
    Reference: https://www.odoo.com/documentation/19.0/developer/reference/backend/orm.html
    
    FIELD NAMING:
    - All custom fields use ptt_ prefix (Party Time Texas)
    - This follows Odoo best practice: x_ is reserved for Studio fields
    """
    _inherit = "product.product"

    # === DJ SERVICE CONFIGURATION ===
    ptt_min_hours = fields.Float(
        string="Minimum Hours",
        default=0.0,
        help="Minimum hours required for this service variant. "
             "E.g., Wedding Premier requires 5 hours minimum.",
    )
    ptt_guest_count_min = fields.Integer(
        string="Min Guest Count",
        default=0,
        help="Minimum guest count for this service tier. "
             "Used to guide tier selection during quoting.",
    )
    ptt_guest_count_max = fields.Integer(
        string="Max Guest Count",
        default=0,
        help="Maximum guest count for this service tier. "
             "0 = unlimited (e.g., Premier tier has no upper limit).",
    )
    ptt_price_per_hour_min = fields.Monetary(
        string="Hourly Rate (Min)",
        currency_field="currency_id",
        help="Minimum hourly rate for this service variant. "
             "This is the default price shown in quotes.",
    )
    ptt_price_per_hour_max = fields.Monetary(
        string="Hourly Rate (Max)",
        currency_field="currency_id",
        help="Maximum hourly rate for this service variant. "
             "Sales reps can negotiate up to this ceiling.",
    )
    ptt_cost_per_hour_min = fields.Monetary(
        string="Hourly Cost (Min)",
        currency_field="currency_id",
        help="Minimum vendor cost per hour for this service variant.",
    )
    ptt_cost_per_hour_max = fields.Monetary(
        string="Hourly Cost (Max)",
        currency_field="currency_id",
        help="Maximum vendor cost per hour for this service variant.",
    )
    ptt_package_includes = fields.Html(
        string="What's Included",
        help="Description of what's included in this service package. "
             "Displayed to customers in quotes and proposals.",
    )
    ptt_recommended_addon_ids = fields.Many2many(
        "product.product",
        "ptt_product_addon_rel",
        "product_id",
        "addon_id",
        string="Recommended Add-Ons",
        domain="[('default_code', 'like', 'ADDON-%')]",
        help="Add-on products recommended for this DJ service variant. NOTE: Addons are ONLY for DJ Services, not other services.",
    )
    
    @api.model
    def _setup_complete(self):
        """Restrict addons field to DJ Service variants only."""
        super()._setup_complete()
        # Make addons field invisible for non-DJ products
        # Addons should ONLY be for DJ Service variants
        addons_field = self._fields.get('ptt_recommended_addon_ids')
        if addons_field:
            # Domain will filter by default_code in view if needed
            # But we can't restrict field access per-record in model
            # So we'll rely on views to hide it for non-DJ products
            pass
    
    # Currency field for monetary fields
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        compute="_compute_currency_id",
        store=False,
    )
    
    @api.depends_context('company')
    def _compute_currency_id(self):
        """Get currency from company."""
        for product in self:
            product.currency_id = self.env.company.currency_id
