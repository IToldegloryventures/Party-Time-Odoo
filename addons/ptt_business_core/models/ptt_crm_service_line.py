from odoo import models, fields, api

from .constants import SERVICE_TYPES, SERVICE_TIERS


class PttCrmServiceLine(models.Model):
    """Service lines for CRM Leads - allows selecting services with tier categories."""
    _name = "ptt.crm.service.line"
    _description = "CRM Lead Service Line"
    _order = "sequence, id"

    lead_id = fields.Many2one(
        "crm.lead",
        string="Lead/Opportunity",
        required=True,
        ondelete="cascade",
        index=True,
    )
    sequence = fields.Integer(string="Sequence", default=10)
    
    # Service Selection - linked to Sales products
    # Exclude addon products (ADDON-%) - addons should not be selectable as main services
    # NOTE: Domain handles null default_code to prevent addons without codes from slipping through
    product_id = fields.Many2one(
        "product.product",
        string="Service/Product",
        domain="[('sale_ok', '=', True), '|', ('default_code', '=', False), ('default_code', 'not ilike', 'ADDON-%')]",
        help="Select a service from the Sales product catalog (addon products are excluded)",
    )
    
    # Tier Category - uses shared constant (migrated from bronze/silver/gold/platinum in v19.0.5.0.0)
    tier = fields.Selection(
        SERVICE_TIERS,
        string="Service Tier",
        default="classic",
        help="Service tier level - Essentials/Classic/Premier. Affects pricing and service quality.",
    )
    
    # Service Type (for quick categorization without product)
    # Uses shared constant to avoid duplication (DRY principle)
    service_type = fields.Selection(
        SERVICE_TYPES,
        string="Service Category",
        help="General service category",
    )
    
    description = fields.Text(string="Description/Notes")
    
    # Pricing
    estimated_price = fields.Monetary(
        string="Estimated Price",
        currency_field="currency_id",
        help="Estimated price to quote the customer",
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )
    
    # Computed display name
    display_name = fields.Char(compute="_compute_display_name", store=True)
    
    @api.depends("product_id", "service_type", "tier")
    def _compute_display_name(self):
        for line in self:
            if line.product_id:
                line.display_name = f"{line.product_id.name} ({line.tier.title() if line.tier else 'N/A'})"
            elif line.service_type:
                service_label = dict(self._fields['service_type'].selection).get(line.service_type, line.service_type)
                line.display_name = f"{service_label} ({line.tier.title() if line.tier else 'N/A'})"
            else:
                line.display_name = f"Service Line ({line.tier.title() if line.tier else 'N/A'})"
