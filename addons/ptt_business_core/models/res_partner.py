from odoo import models, fields


class ResPartner(models.Model):
    """Extend res.partner for PTT vendor management.
    
    NOTE: Use standard Odoo fields where possible:
    - supplier_rank > 0 = Is a Vendor (standard - use instead of x_is_vendor)
    - comment = Internal Notes (standard - use instead of x_vendor_notes)
    
    Custom PTT fields are for vendor-specific data only.
    """
    _inherit = "res.partner"

    # === VENDOR FIELDS (Custom PTT) ===
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
        help="Primary service type this vendor provides. Note: Use supplier_rank > 0 to identify vendors.",
    )
    x_vendor_rating = fields.Selection(
        [
            ("1", "1 Star"),
            ("2", "2 Stars"),
            ("3", "3 Stars"),
            ("4", "4 Stars"),
            ("5", "5 Stars"),
        ],
        string="Rating",
        help="Vendor performance rating",
    )
    x_vendor_preferred = fields.Boolean(
        string="Preferred Vendor",
        help="Mark as preferred vendor for priority assignment",
    )
