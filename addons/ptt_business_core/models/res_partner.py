from odoo import models, fields


class ResPartner(models.Model):
    _inherit = "res.partner"

    # === VENDOR FIELDS ===
    x_is_vendor = fields.Boolean(
        string="Vendor",
        help="Mark this contact as a vendor / service provider.",
    )
    
    # Vendor Detail Fields
    x_vendor_service_types = fields.Selection(
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
        help="Primary service type this vendor provides",
    )
    x_vendor_rating = fields.Selection(
        [
            ("1", "⭐"),
            ("2", "⭐⭐"),
            ("3", "⭐⭐⭐"),
            ("4", "⭐⭐⭐⭐"),
            ("5", "⭐⭐⭐⭐⭐"),
        ],
        string="Rating",
        help="Vendor performance rating",
    )
    x_vendor_notes = fields.Text(
        string="Vendor Notes",
        help="Additional notes about this vendor",
    )
    x_vendor_preferred = fields.Boolean(
        string="Preferred Vendor",
        help="Mark as preferred vendor for priority assignment",
    )


