# -*- coding: utf-8 -*-
# Part of Party Time Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ProjectTask(models.Model):
    """Extend project.task for PTT event management.
    
    NOTE: All event context (date, venue, client, etc.) should be accessed 
    via task.project_id - no need for redundant related fields.
    
    Access event data via: task.project_id.x_studio_event_date, task.project_id.x_studio_venue_name, etc.
    
    FIELD NAMING:
    - Genuine PTT fields use ptt_ prefix (Party Time Texas)
    - Studio fields (x_studio_*) are used directly without aliases
    """
    _inherit = "project.task"

    ptt_event_id = fields.Char(
        string="Event ID",
        related="project_id.ptt_event_id",
        store=True,
        readonly=True,
        help="Event ID from the linked project.",
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

