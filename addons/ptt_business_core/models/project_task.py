from odoo import models, fields, api, _


class ProjectTask(models.Model):
    """Extend project.task for PTT event management.
    
    NOTE: All event context (date, venue, client, etc.) should be accessed 
    via task.project_id - no need for redundant related fields.
    
    Access event data via: task.project_id.ptt_event_date, task.project_id.ptt_venue_name, etc.
    
    FIELD NAMING:
    - All custom fields use ptt_ prefix (Party Time Texas)
    - This follows Odoo best practice: x_ is reserved for Studio fields
    """
    _inherit = "project.task"

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
