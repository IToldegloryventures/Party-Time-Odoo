from odoo import models, fields, api


class PttPersonalTodo(models.Model):
    """Personal To-Do items for individual users.
    
    This is a lightweight personal task model completely separate from project.task.
    Users can add misc items that don't belong to any project.
    """
    _name = "ptt.personal.todo"
    _description = "Personal To-Do Item"
    _order = "sequence, due_date, id"
    _rec_name = "name"

    # Owner
    user_id = fields.Many2one(
        "res.users",
        string="Owner",
        required=True,
        default=lambda self: self.env.user,
        index=True,
        ondelete="cascade",
        help="User who owns this personal to-do item."
    )
    
    # Core fields
    name = fields.Char(
        string="To-Do",
        required=True,
        help="Short description of the to-do item."
    )
    description = fields.Text(
        string="Notes",
        help="Additional details or notes."
    )
    
    # Scheduling
    due_date = fields.Date(
        string="Due Date",
        index=True,
        help="Optional due date for this item."
    )
    
    # Priority & Status
    priority = fields.Selection(
        [
            ("0", "Low"),
            ("1", "Normal"),
            ("2", "High"),
            ("3", "Urgent"),
        ],
        string="Priority",
        default="1",
        help="Priority level of this to-do item."
    )
    is_done = fields.Boolean(
        string="Done",
        default=False,
        help="Mark as completed."
    )
    
    # Ordering
    sequence = fields.Integer(
        string="Sequence",
        default=10,
        help="Used to order items in the list."
    )
    
    # Computed category for display grouping
    ptt_category = fields.Selection(
        [
            ("today", "Today"),
            ("overdue", "Overdue"),
            ("upcoming", "Upcoming"),
            ("unscheduled", "Unscheduled"),
        ],
        string="Category",
        compute="_compute_category",
        store=False,
        help="Computed category based on due date. Used for grouping to-do items in the UI."
    )
    
    @api.depends("due_date", "is_done")
    def _compute_category(self):
        """Compute category based on due_date vs today."""
        today = fields.Date.context_today(self)
        for record in self:
            if record.is_done:
                record.ptt_category = False
            elif not record.due_date:
                record.ptt_category = "unscheduled"
            elif record.due_date < today:
                record.ptt_category = "overdue"
            elif record.due_date == today:
                record.ptt_category = "today"
            else:
                record.ptt_category = "upcoming"
    
    def action_toggle_done(self):
        """Toggle the done status of the to-do item."""
        for record in self:
            record.is_done = not record.is_done
        return True
    
    def action_mark_done(self):
        """Mark the to-do item as done."""
        self.write({"is_done": True})
        return True
    
    def action_mark_undone(self):
        """Mark the to-do item as not done."""
        self.write({"is_done": False})
        return True
    
    @api.model
    def get_my_todos(self):
        """Get all to-do items for the current user, grouped by category.
        
        Returns a dict with action metadata for deep linking.
        """
        todos = self.search([
            ("user_id", "=", self.env.user.id),
            ("is_done", "=", False),
        ])
        
        result = {
            "today": [],
            "overdue": [],
            "upcoming": [],
            "unscheduled": [],
        }
        
        for todo in todos:
            todo_data = {
                "id": todo.id,
                "name": todo.name,
                "description": todo.description or "",
                "due_date": todo.due_date.isoformat() if todo.due_date else False,
                "priority": todo.priority,
                "sequence": todo.sequence,
            }
            if todo.ptt_category:
                result[todo.ptt_category].append(todo_data)
        
        return result

