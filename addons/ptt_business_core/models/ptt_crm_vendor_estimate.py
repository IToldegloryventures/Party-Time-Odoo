from odoo import models, fields, api


class PttCrmVendorEstimate(models.Model):
    """Estimated vendor costs for CRM opportunities."""
    _name = "ptt.crm.vendor.estimate"
    _description = "CRM Lead Vendor Cost Estimate"

    crm_lead_id = fields.Many2one(
        "crm.lead",
        string="Opportunity",
        required=True,
        ondelete="cascade",
        index=True,
    )
    service_type = fields.Selection(
        [
            ("dj", "DJ/MC Services"),
            ("photovideo", "Photo/Video"),
            ("live_entertainment", "Live Entertainment"),
            ("lighting", "Lighting/AV"),
            ("decor", "Decor/Thematic Design"),
            ("photobooth", "Photo Booth"),
            ("caricature", "Caricature Artists"),
            ("casino", "Casino Services"),
            ("catering", "Catering"),
            ("transportation", "Transportation"),
            ("rentals", "Rentals (Other)"),
            ("staffing", "Staffing"),
            ("venue_sourcing", "Venue Sourcing"),
            ("coordination", "Event Coordination"),
            ("other", "Other"),
        ],
        string="Service Type",
        required=True,
    )
    
    vendor_id = fields.Many2one(
        "res.partner",
        string="Vendor",
        domain="[('x_is_vendor', '=', True)]",
        help="Optional: Link to actual vendor (for by-name requests)",
    )
    
    pricing_tier = fields.Selection(
        [
            ("essential", "Essential"),
            ("classic", "Classic"),
            ("premier", "Premier"),
            ("byname", "By-Name Request"),
        ],
        string="Pricing Tier",
        default="classic",
        help="Pricing tier for this service estimate",
    )
    
    x_vendor_name = fields.Char(
        string="Vendor Name (Estimated)",
        help="Name of vendor we expect to use",
    )
    
    estimated_cost = fields.Monetary(
        string="Estimated Cost",
        currency_field="currency_id",
        required=True,
        help="Estimated cost we will pay to this vendor",
    )
    
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        related="crm_lead_id.company_currency",
        store=True,
        readonly=True,
    )

    _order = "id"
    
    @api.onchange("vendor_id", "service_type", "pricing_tier")
    def _onchange_vendor_pricing(self):
        """Auto-fill estimated_cost from vendor service pricing."""
        if self.vendor_id and self.service_type and self.pricing_tier:
            service = self.vendor_id.x_vendor_service_ids.filtered(
                lambda s: s.service_type == self.service_type
            )
            if service:
                tier_field = f"price_{self.pricing_tier}"
                self.estimated_cost = getattr(service, tier_field, 0)
                self.x_vendor_name = self.vendor_id.name

