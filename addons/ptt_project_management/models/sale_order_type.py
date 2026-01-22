# Part of Party Time Texas Event Management System
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
"""
Extend sale.order.type with native Odoo project template integration.

This links event types to native Odoo project templates (project.project 
with is_template=True) so the Event Kickoff product can dynamically
select the correct template based on the Sale Order's event type.

Templates are defined in ptt_business_core/data/project_template.xml:
- project_template_corporate
- project_template_wedding
- project_template_social
"""

from odoo import models, fields


class SaleOrderType(models.Model):
    """Extend Sale Order Type with Native Project Template link."""
    _inherit = 'sale.order.type'

    # Native Odoo project template (project.project with is_template=True)
    native_project_template_id = fields.Many2one(
        'project.project',
        string="Project Template",
        domain=[('is_template', '=', True)],
        help="Native Odoo project template to use when creating projects for this event type. "
             "The Event Kickoff product will use this template when creating the event project."
    )
