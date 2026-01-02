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
        ondelete="set null",
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
    
    # Vendor Status Tracking Fields
    x_status = fields.Selection(
        [
            ("pending", "Pending"),
            ("confirmed", "Confirmed"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="pending",
        help="Track the status of this vendor assignment",
    )
    x_confirmed_date = fields.Date(
        string="Confirmed Date",
        help="Date when vendor confirmed their assignment",
    )
    x_contact_person = fields.Char(
        string="Contact Person",
        help="Name of the contact person for this vendor assignment",
    )
    x_contact_phone = fields.Char(
        string="Contact Phone",
        help="Phone number for vendor contact person",
    )
    x_arrival_time = fields.Char(
        string="Arrival Time",
        help="Expected arrival/setup time for vendor",
    )
    x_equipment_notes = fields.Text(
        string="Equipment Notes",
        help="Notes about equipment, setup requirements, or special instructions",
    )

    _order = "id"

