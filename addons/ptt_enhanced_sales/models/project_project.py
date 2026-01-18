# Part of Party Time Texas Event Management System
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import models, fields


class ProjectProject(models.Model):
    """Extend project with event type link from sale.order.type."""
    _inherit = 'project.project'

    ptt_event_type_id = fields.Many2one(
        'sale.order.type',
        string="Event Type",
        help="Event type classification (Corporate, Wedding, Social, etc.)"
    )
