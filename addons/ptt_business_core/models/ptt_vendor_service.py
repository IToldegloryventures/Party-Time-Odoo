from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PttVendorService(models.Model):
    """Vendor service pricing with Essential/Classic/Premier tiers"""
    _name = "ptt.vendor.service"
    _description = "Vendor Service Pricing"
    _order = "vendor_id, service_type"

    vendor_id = fields.Many2one(
        "res.partner",
        string="Vendor",
        required=True,
        ondelete="cascade",
        domain="[('x_is_vendor', '=', True)]",
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
        help="Type of service this vendor provides",
    )
    
    # Pricing Tiers
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
        required=True,
    )
    
    price_essential = fields.Monetary(
        string="Essential Tier",
        currency_field="currency_id",
        help="Base pricing for Essential tier events",
    )
    
    price_classic = fields.Monetary(
        string="Classic Tier",
        currency_field="currency_id",
        help="Pricing for Classic tier events",
    )
    
    price_premier = fields.Monetary(
        string="Premier Tier",
        currency_field="currency_id",
        help="Premium pricing for Premier tier events",
    )
    
    price_byname = fields.Monetary(
        string="By-Name Request",
        currency_field="currency_id",
        help="Pricing when vendor is specifically requested by name",
    )
    
    # Service-level restrictions
    restriction_ids = fields.Many2many(
        "ptt.vendor.restriction",
        string="Service Restrictions",
        help="Restrictions specific to this service (vs vendor-wide)",
    )
    
    notes = fields.Text(
        string="Pricing Notes",
        help="Additional notes about pricing for this service",
    )
    
    @api.constrains("vendor_id", "service_type")
    def _check_unique_vendor_service(self):
        """Ensure each vendor can only have one pricing entry per service type."""
        for record in self:
            existing = self.search([
                ("vendor_id", "=", record.vendor_id.id),
                ("service_type", "=", record.service_type),
                ("id", "!=", record.id),
            ])
            if existing:
                raise ValidationError(
                    _("Each vendor can only have one pricing entry per service type.")
                )
