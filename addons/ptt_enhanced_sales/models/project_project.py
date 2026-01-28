# Part of Party Time Texas Event Management System
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import models, fields


class ProjectProject(models.Model):
    """Extend project with event type link from sale.order.type."""
    _inherit = 'project.project'

    # Event Type - defined here because sale.order.type is in ptt_enhanced_sales
    # This field links to the CRM lead's event type via the related chain
    ptt_event_type_id = fields.Many2one(
        "sale.order.type",
        related="ptt_crm_lead_id.ptt_event_type_id",
        string="Event Type",
        store=True,
        readonly=False,
        depends=['ptt_crm_lead_id'],
        help="Event type template from the linked CRM opportunity"
    )
