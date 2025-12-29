from odoo import models, fields


class ResPartner(models.Model):
    _inherit = "res.partner"

    x_is_vendor = fields.Boolean(
        string="Vendor",
        help="Mark this contact as a vendor / service provider.",
    )
    
    # Vendor Detail Fields
    x_vendor_service_types = fields.Selection(
        [
            ("dj", "DJ/MC"),
            ("lighting", "Lighting/AV"),
            ("photobooth", "Photo Booth"),
            ("live_entertainment", "Live Entertainment"),
            ("catering", "Catering"),
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


