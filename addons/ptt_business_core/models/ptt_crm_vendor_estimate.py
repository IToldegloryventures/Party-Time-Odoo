from odoo import models, fields


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
    vendor_name = fields.Char(string="Vendor Name (Estimated)", help="Name of vendor we expect to use")
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

    _order = "service_type, id"

