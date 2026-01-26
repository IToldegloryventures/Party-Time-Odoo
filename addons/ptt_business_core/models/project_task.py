# -*- coding: utf-8 -*-
# Part of Party Time Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ProjectTask(models.Model):
    """Extend project.task for PTT event management.
    
    NOTE: All event context (date, venue, client, etc.) should be accessed 
    via task.project_id - no need for redundant related fields.
    
    Access event data via: task.project_id.ptt_event_date, task.project_id.ptt_venue_name, etc.
    
    FIELD NAMING:
    - All PTT fields use ptt_ prefix (Party Time Texas)
    """
    _inherit = "project.task"

    # =========================================================================
    # DEADLINE CONFIGURATION FIELDS
    # Required by project_template.xml data file
    # =========================================================================
    ptt_deadline_reference = fields.Selection(
        selection=[
            ('confirmation', 'From SO Confirmation'),
            ('event', 'From Event Date'),
        ],
        string="Deadline Reference",
        default='event',
        help="Which date to calculate the deadline from:\n"
             "- SO Confirmation: Uses sale_order.date_order\n"
             "- Event Date: Uses sale_order.event_date"
    )

    ptt_deadline_offset_days = fields.Integer(
        string="Deadline Offset (Days)",
        default=0,
        help="Number of days from the reference date:\n"
             "- Positive: days AFTER the reference (e.g., +7 = 1 week after)\n"
             "- Negative: days BEFORE the reference (e.g., -14 = 2 weeks before)"
    )

    # === ACTION METHODS ===
    
    def action_view_project(self):
        """Open the related project form view."""
        self.ensure_one()
        if not self.project_id:
            return False
        return {
            "type": "ir.actions.act_window",
            "name": _("Project"),
            "res_model": "project.project",
            "res_id": self.project_id.id,
            "view_mode": "form",
            "target": "current",
        }

