from odoo import models, fields, api


class ProjectTask(models.Model):
    """Extend project.task with computed category for My Work section."""
    _inherit = "project.task"

    x_task_category = fields.Selection(
        [
            ("today", "Today"),
            ("overdue", "Overdue"),
            ("upcoming", "Upcoming"),
            ("unscheduled", "Unscheduled"),
        ],
        string="Task Category",
        compute="_compute_task_category",
        store=False,
        help="Computed category based on due date vs today. Used for My Work grouping."
    )

    @api.depends("date_deadline")
    def _compute_task_category(self):
        """Compute category based on date_deadline vs today."""
        today = fields.Date.context_today(self)
        for task in self:
            if not task.date_deadline:
                task.x_task_category = "unscheduled"
            elif task.date_deadline < today:
                task.x_task_category = "overdue"
            elif task.date_deadline == today:
                task.x_task_category = "today"
            else:
                task.x_task_category = "upcoming"

