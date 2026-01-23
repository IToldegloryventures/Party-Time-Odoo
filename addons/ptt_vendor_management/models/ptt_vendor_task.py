"""
PTT Vendor Task Model

Tasks that can be assigned to vendors for their work order assignments.
These are simple tasks (not Odoo project.task) specifically for vendor portal.

Reference: https://www.odoo.com/documentation/19.0/developer/tutorials/server_framework_101/
"""
from odoo import api, fields, models, _


class PTTVendorTask(models.Model):
    """Simple task model for vendor assignments.
    
    Allows staff to assign specific tasks to vendors that they can
    view and mark complete from the portal.
    """
    _name = "ptt.vendor.task"
    _description = "Vendor Task"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "sequence, id"
    
    name = fields.Char(
        string="Task",
        required=True,
        tracking=True,
    )
    
    description = fields.Html(
        string="Description",
        help="Detailed instructions for this task",
    )
    
    assignment_id = fields.Many2one(
        "ptt.project.vendor.assignment",
        string="Work Order",
        required=True,
        ondelete="cascade",
        index=True,
    )
    
    vendor_id = fields.Many2one(
        "res.partner",
        string="Vendor",
        related="assignment_id.vendor_id",
        store=True,
        readonly=True,
    )
    
    project_id = fields.Many2one(
        "project.project",
        string="Event/Project",
        related="assignment_id.project_id",
        store=True,
        readonly=True,
    )
    
    sequence = fields.Integer(
        string="Sequence",
        default=10,
    )
    
    due_date = fields.Date(
        string="Due Date",
        help="When this task should be completed",
    )
    
    state = fields.Selection(
        [
            ("todo", "To Do"),
            ("in_progress", "In Progress"),
            ("done", "Done"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="todo",
        tracking=True,
    )
    
    priority = fields.Selection(
        [
            ("0", "Normal"),
            ("1", "Important"),
            ("2", "Urgent"),
        ],
        string="Priority",
        default="0",
    )
    
    completed_date = fields.Datetime(
        string="Completed Date",
        readonly=True,
    )
    
    vendor_notes = fields.Text(
        string="Vendor Notes",
        help="Notes from the vendor about this task",
    )
    
    # === ACTIONS ===
    
    def action_start(self):
        """Mark task as in progress."""
        self.write({'state': 'in_progress'})
        return True
    
    def action_done(self):
        """Mark task as completed."""
        self.write({
            'state': 'done',
            'completed_date': fields.Datetime.now(),
        })
        # Notify on the assignment
        self.assignment_id.message_post(
            body=_("Task completed: %s") % self.name,
            message_type='notification',
        )
        return True
    
    def action_cancel(self):
        """Cancel this task."""
        self.write({'state': 'cancelled'})
        return True
    
    def action_reopen(self):
        """Reopen a completed/cancelled task."""
        self.write({
            'state': 'todo',
            'completed_date': False,
        })
        return True
