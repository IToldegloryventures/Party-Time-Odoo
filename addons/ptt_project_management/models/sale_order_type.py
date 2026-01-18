# Part of Party Time Texas Event Management System
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
"""
Extend sale.order.type with project template integration.

This field is defined here (not in ptt_enhanced_sales) to avoid
circular dependency, since project.template is defined in this module.
"""

from odoo import models, fields


class SaleOrderType(models.Model):
    """Extend Sale Order Type with Project Template link."""
    _inherit = 'sale.order.type'

    project_template_id = fields.Many2one(
        'project.template',
        string="Default Project Template",
        help="Template to use when creating projects for this event type"
    )
