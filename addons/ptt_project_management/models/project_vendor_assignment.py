# Part of Party Time Texas Event Management System
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
"""
Project Vendor Assignment Extensions for Project Management.

The base model ptt.project.vendor.assignment is defined in ptt_business_core.
This module extends it with project management specific functionality.
"""

from odoo import models, fields, api
from odoo.addons.ptt_business_core.constants import PERFORMANCE_RATINGS


class PttProjectVendorAssignmentExtended(models.Model):
    """Extended Vendor Assignment with project management features."""
    _inherit = "ptt.project.vendor.assignment"
    
    # Additional project management fields
    task_ids = fields.One2many(
        "project.task",
        "ptt_vendor_assignment_id",
        string="Related Tasks",
        help="Tasks assigned to this vendor for this service"
    )
    task_count = fields.Integer(
        string="Task Count",
        compute="_compute_task_count",
    )
    
    # Schedule tracking
    scheduled_start = fields.Datetime(
        string="Scheduled Start",
        help="Scheduled start time for this vendor's service"
    )
    scheduled_end = fields.Datetime(
        string="Scheduled End",
        help="Scheduled end time for this vendor's service"
    )
    
    # Performance tracking
    performance_rating = fields.Selection(
        PERFORMANCE_RATINGS,
        string="Performance Rating"
    )
    performance_notes = fields.Text(string="Performance Notes")
    
    @api.depends("task_ids")
    def _compute_task_count(self):
        """Compute count of tasks linked to this vendor assignment."""
        for record in self:
            record.task_count = len(record.task_ids)
    
    def action_view_tasks(self):
        """View tasks related to this vendor assignment."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Vendor Tasks',
            'res_model': 'project.task',
            'view_mode': 'list,form',
            'domain': [('ptt_vendor_assignment_id', '=', self.id)],
            'context': {
                'default_ptt_vendor_assignment_id': self.id,
                'default_project_id': self.project_id.id,
            },
        }


class ProjectTask(models.Model):
    """Extend project task with vendor assignment link."""
    _inherit = "project.task"
    
    ptt_vendor_assignment_id = fields.Many2one(
        "ptt.project.vendor.assignment",
        string="Vendor Assignment",
        help="Link to the vendor assignment for this task"
    )