from odoo import models, fields


class ResPartner(models.Model):
    _inherit = "res.partner"

    x_is_vendor = fields.Boolean(
        string="Is Vendor",
        help="Mark this contact as a vendor / service provider.",
    )


