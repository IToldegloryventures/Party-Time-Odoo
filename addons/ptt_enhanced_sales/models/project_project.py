# Part of Party Time Texas Event Management System
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import models, fields


class ProjectProject(models.Model):
    """Extend project with event type from CRM Lead."""
    _inherit = 'project.project'

    # ==========================================================================
    # EVENT TYPE - Related from CRM Lead (READ-ONLY)
    # ==========================================================================
    # CRM Lead is the ONLY place to set event type.
    # Project displays it as read-only via related field.
    # Auto-syncs when CRM Lead event type changes.
    
    ptt_event_type = fields.Selection(
        related='ptt_crm_lead_id.ptt_event_type',
        string="Event Type",
        store=True,
        readonly=True,
        help="Event type (Corporate/Social/Wedding) - edit in CRM Lead. "
             "Used for filtering, grouping, and calendar coloring.",
    )
