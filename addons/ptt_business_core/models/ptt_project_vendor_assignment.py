from odoo import models, fields


class PttProjectVendorAssignment(models.Model):
    """Actual vendor assignments and costs for projects."""
    _name = "ptt.project.vendor.assignment"
    _description = "Project Vendor Assignment"

    project_id = fields.Many2one(
        "project.project",
        string="Project",
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
        help="Actual vendor assigned for this service",
    )
    actual_cost = fields.Monetary(
        string="Actual Cost",
        currency_field="currency_id",
        required=True,
        help="Actual cost we pay to this vendor",
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        related="project_id.currency_id",
        readonly=True,
    )
    notes = fields.Text(string="Notes")

    _order = "service_type, id"

