from odoo import models, fields, api

from .constants import SERVICE_TYPES


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
    # Uses shared constant to avoid duplication (DRY principle)
    service_type = fields.Selection(
        SERVICE_TYPES,
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
        compute="_compute_currency_id",
        store=True,
        readonly=True,
    )
    notes = fields.Text(string="Notes")
    
    @api.depends('project_id.currency_id')
    def _compute_currency_id(self):
        """Compute currency with company fallback.
        
        Pattern matches project.project._compute_currency_id in Odoo core.
        Reference: https://www.odoo.com/documentation/19.0/developer/reference/backend/orm.html#computed-fields
        """
        for record in self:
            record.currency_id = (
                record.project_id.currency_id or self.env.company.currency_id
            )
    
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
