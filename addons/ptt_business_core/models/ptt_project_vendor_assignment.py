from odoo import models, fields


class PttProjectVendorAssignment(models.Model):
    """Actual vendor assignments and costs for projects.
    
    FIELD NAMING:
    - All custom fields use ptt_ prefix (Party Time Texas)
    - This follows Odoo best practice: x_ is reserved for Studio fields
    """
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
            ("dj", "DJ & MC Services"),
            ("photovideo", "Photo/Video"),
            ("live_entertainment", "Live Entertainment"),
            ("lighting", "Lighting/AV"),
            ("decor", "Decor/Thematic Design"),
            ("photobooth", "Photo Booth"),
            ("caricature", "Caricature Artist"),
            ("casino", "Casino Services"),
            ("catering", "Catering & Bartender Services"),
            ("transportation", "Transportation"),
            ("rentals", "Rentals (Other)"),
            ("staffing", "Staffing"),
            ("venue_sourcing", "Venue Sourcing"),
            ("coordination", "Event Planning Services"),
            ("other", "Other"),
        ],
        string="Service Type",
        required=True,
    )
    vendor_id = fields.Many2one(
        "res.partner",
        string="Vendor",
        domain="[('supplier_rank', '>', 0)]",
        ondelete="set null",
        help="Actual vendor assigned for this service. Uses standard Odoo supplier_rank field.",
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
    
    # Vendor Status Tracking Fields (renamed from x_ to ptt_ prefix)
    ptt_status = fields.Selection(
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
    ptt_confirmed_date = fields.Date(
        string="Confirmed Date",
        help="Date when vendor confirmed their assignment",
    )
    ptt_contact_person = fields.Char(
        string="Contact Person",
        help="Name of the contact person for this vendor assignment",
    )
    ptt_contact_phone = fields.Char(
        string="Contact Phone",
        help="Phone number for vendor contact person",
    )
    ptt_arrival_time = fields.Char(
        string="Arrival Time",
        help="Expected arrival/setup time for vendor",
    )
    ptt_equipment_notes = fields.Text(
        string="Equipment Notes",
        help="Notes about equipment, setup requirements, or special instructions",
    )

    _order = "id"
