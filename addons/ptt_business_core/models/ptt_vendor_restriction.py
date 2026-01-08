from odoo import models, fields


class PttVendorRestriction(models.Model):
    """Event type restrictions for vendors (no schools, no bar mitzvahs, etc.)"""
    _name = "ptt.vendor.restriction"
    _description = "Vendor Event Type Restriction"
    _order = "sequence, name"

    name = fields.Char(
        string="Restriction Name",
        required=True,
        help="e.g., No School Events, No Bar/Bat Mitzvahs",
    )
    
    code = fields.Char(
        string="Code",
        required=True,
        help="e.g., no_school, no_barmitzvah",
    )
    
    description = fields.Text(
        string="Description",
        help="Explanation of why this restriction exists",
    )
    
    sequence = fields.Integer(
        default=10,
        help="Display order",
    )
    
    active = fields.Boolean(
        default=True,
        help="If unchecked, this restriction will be hidden",
    )
