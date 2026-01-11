from odoo import models, fields


class PttVendorServiceTag(models.Model):
    """Service tags for categorizing vendor capabilities.
    
    Used to tag vendors with the services they provide (DJ, Photography, etc.)
    for filtering and assignment purposes.
    """
    _name = "ptt.vendor.service.tag"
    _description = "Vendor Service Tag"
    _order = "sequence, name"

    name = fields.Char(
        string="Service Name",
        required=True,
        help="Name of the service category (e.g., DJ, Photography)",
    )
    code = fields.Char(
        string="Code",
        help="Short code for the service (e.g., 'dj', 'photo')",
    )
    sequence = fields.Integer(
        string="Sequence",
        default=10,
        help="Used to order services in lists",
    )
    color = fields.Integer(
        string="Color",
        default=0,
        help="Color index for tag display",
    )
    active = fields.Boolean(
        string="Active",
        default=True,
        help="If unchecked, the service tag will be hidden",
    )
    description = fields.Text(
        string="Description",
        help="Detailed description of this service category",
    )
    
    # Computed field for vendor count
    vendor_count = fields.Integer(
        string="# Vendors",
        compute="_compute_vendor_count",
        help="Number of vendors tagged with this service",
    )
    
    def _compute_vendor_count(self):
        """Count vendors tagged with this service."""
        for tag in self:
            tag.vendor_count = self.env["res.partner"].search_count([
                ("x_vendor_service_tag_ids", "in", tag.id),
                ("supplier_rank", ">", 0),
            ])
