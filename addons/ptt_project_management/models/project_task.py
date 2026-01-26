# Part of Party Time Texas. See LICENSE file for full copyright and licensing details.
"""
Project Task enhancements for deadline calculation and parent blocking.

Deadline Calculation:
- Tasks have a reference type (from SO confirmation OR from event date)
- Tasks have an offset in days (positive = after, negative = before)
- Deadlines auto-calculate when SO is confirmed or event date changes

Parent Blocking:
- Parent tasks cannot be completed if subtasks are still open
- Subtasks can be marked as N/A (not applicable) to skip them
"""

from datetime import timedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ProjectTask(models.Model):
    """Extended project.task with deadline calculation and blocking."""
    _inherit = 'project.task'

    # =========================================================================
    # DEADLINE CONFIGURATION FIELDS
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

    ptt_deadline_auto_calculated = fields.Boolean(
        string="Auto-Calculated Deadline",
        default=False,
        help="True if deadline was auto-calculated (can still be manually overridden)"
    )

    # =========================================================================
    # SUBTASK N/A MARKING (for parent blocking)
    # =========================================================================
    ptt_marked_na = fields.Boolean(
        string="Not Applicable",
        default=False,
        help="Mark this subtask as N/A for this specific event. "
             "N/A subtasks don't block parent task completion."
    )

    # =========================================================================
    # COMPUTED FIELDS FOR DISPLAY
    # =========================================================================
    ptt_subtask_progress = fields.Float(
        string="Subtask Progress",
        compute="_compute_subtask_progress",
        store=True,
        help="Percentage of subtasks completed (0-100)"
    )

    ptt_subtask_summary = fields.Char(
        string="Subtasks",
        compute="_compute_subtask_progress",
        store=True,
        help="Summary like '3/5 complete'"
    )

    ptt_is_overdue = fields.Boolean(
        string="Overdue",
        compute="_compute_is_overdue",
        search="_search_is_overdue",
        help="True if deadline has passed and task is not complete"
    )

    ptt_days_until_deadline = fields.Integer(
        string="Days Until Deadline",
        compute="_compute_days_until_deadline",
        help="Number of days until deadline (negative if overdue)"
    )

    # =========================================================================
    # BLOCKER-AWARE DEADLINE (Based on MJM project_task_deadline)
    # Uses Odoo 19 native depend_on_ids field
    # =========================================================================
    ptt_blocked_by_deadline = fields.Date(
        string="Blocked Until",
        compute="_compute_blocked_by_deadline",
        help="Latest deadline of blocking tasks. This task shouldn't start before this date."
    )

    ptt_has_deadline_conflict = fields.Boolean(
        string="Deadline Conflict",
        compute="_compute_blocked_by_deadline",
        help="True if this task's deadline is before its blocker's deadline."
    )

    # =========================================================================
    # COMPUTED METHODS
    # =========================================================================
    @api.depends('child_ids', 'child_ids.state', 'child_ids.ptt_marked_na')
    def _compute_subtask_progress(self):
        """Compute subtask completion progress.

        Uses Odoo 19 native `is_closed` field which checks if state is in CLOSED_STATES
        ('1_done', '1_canceled').
        """
        for task in self:
            children = task.child_ids
            if not children:
                task.ptt_subtask_progress = 0.0
                task.ptt_subtask_summary = ""
                continue

            # Count completed (is_closed=True) or marked N/A
            total = len(children)
            complete = len(children.filtered(
                lambda t: t.is_closed or t.ptt_marked_na
            ))

            task.ptt_subtask_progress = (complete / total * 100) if total else 0.0
            task.ptt_subtask_summary = f"{complete}/{total} complete"

    @api.depends('date_deadline', 'state')
    def _compute_is_overdue(self):
        """Check if task is overdue.

        Uses Odoo 19 native `is_closed` field which checks if state is in CLOSED_STATES.
        """
        today = fields.Date.today()
        for task in self:
            if task.is_closed:  # Already complete (state in CLOSED_STATES)
                task.ptt_is_overdue = False
            elif not task.date_deadline:
                task.ptt_is_overdue = False
            else:
                deadline_date = task.date_deadline
                if hasattr(deadline_date, 'date'):
                    deadline_date = deadline_date.date()
                task.ptt_is_overdue = deadline_date < today

    def _search_is_overdue(self, operator, value):
        """Search for overdue tasks using Odoo 19 state field."""
        today = fields.Date.context_today(self)
        base = [('state', 'not in', ['1_done', '1_canceled'])]
        if operator in ('=', '=='):
            if value:
                return base + [('date_deadline', '<', today)]
            return ['|', ('date_deadline', '=', False), ('date_deadline', '>=', today)]
        if operator in ('!=', '<>'):
            # Not value flips the meaning
            flipped = not bool(value)
            if flipped:
                return base + [('date_deadline', '<', today)]
            return ['|', ('date_deadline', '=', False), ('date_deadline', '>=', today)]
        # Fallback to default behavior for other operators
        return super()._search_is_overdue(operator, value)

    @api.depends('date_deadline')
    def _compute_days_until_deadline(self):
        """Compute days until deadline."""
        today = fields.Date.today()
        for task in self:
            if not task.date_deadline:
                task.ptt_days_until_deadline = 0
            else:
                deadline_date = task.date_deadline
                if hasattr(deadline_date, 'date'):
                    deadline_date = deadline_date.date()
                delta = deadline_date - today
                task.ptt_days_until_deadline = delta.days

    @api.depends('depend_on_ids', 'depend_on_ids.date_deadline', 'date_deadline')
    def _compute_blocked_by_deadline(self):
        """Compute the latest deadline from blocking tasks.

        Based on MJM project_task_deadline/models/project_task.py compute_blocker_date()
        Uses Odoo 19 native depend_on_ids field.
        """
        for task in self:
            max_blocker_date = False
            has_conflict = False

            # Find the latest deadline among blocking tasks
            for blocker in task.depend_on_ids:
                if blocker.date_deadline:
                    blocker_date = blocker.date_deadline
                    if hasattr(blocker_date, 'date'):
                        blocker_date = blocker_date.date()

                    if not max_blocker_date or blocker_date > max_blocker_date:
                        max_blocker_date = blocker_date

            # Check if our deadline is before the blocker's deadline
            if max_blocker_date and task.date_deadline:
                task_deadline = task.date_deadline
                if hasattr(task_deadline, 'date'):
                    task_deadline = task_deadline.date()
                has_conflict = task_deadline < max_blocker_date

            task.ptt_blocked_by_deadline = max_blocker_date
            task.ptt_has_deadline_conflict = has_conflict

    # =========================================================================
    # PARENT TASK BLOCKING CONSTRAINT
    # =========================================================================
    @api.constrains('state')
    def _check_subtasks_complete_before_parent(self):
        """Prevent completing parent task if subtasks are still open.

        Uses Odoo 19 native state field - CLOSED_STATES = {'1_done', '1_canceled'}.

        A subtask is considered "open" if:
        - It is NOT closed (state not in CLOSED_STATES), AND
        - It is NOT marked as N/A
        """
        for task in self:
            # Only check when moving to a closed state (Done or Canceled)
            if not task.is_closed:
                continue

            # Only check if this task has children
            if not task.child_ids:
                continue

            # Find incomplete subtasks (not closed AND not N/A)
            incomplete = task.child_ids.filtered(
                lambda t: not t.is_closed and not t.ptt_marked_na
            )

            if incomplete:
                incomplete_names = ", ".join(incomplete.mapped('name')[:3])
                if len(incomplete) > 3:
                    incomplete_names += f" (+{len(incomplete) - 3} more)"
                raise ValidationError(_(
                    "Cannot complete '%(task)s' - %(count)s subtask(s) still pending:\n%(names)s",
                    task=task.name,
                    count=len(incomplete),
                    names=incomplete_names
                ))

    # =========================================================================
    # DEADLINE CALCULATION METHODS
    # =========================================================================
    def _calculate_deadline_from_sale_order(self, sale_order):
        """Calculate deadline based on sale order dates.

        Args:
            sale_order: The sale.order record to calculate from

        Returns:
            date: The calculated deadline, or False if cannot calculate
        """
        self.ensure_one()

        if not self.ptt_deadline_reference:
            return False

        # Determine the reference date
        if self.ptt_deadline_reference == 'confirmation':
            ref_date = sale_order.date_order
        else:  # 'event'
            ref_date = sale_order.event_date

        if not ref_date:
            return False

        # Convert datetime to date if needed
        if hasattr(ref_date, 'date'):
            ref_date = ref_date.date()

        # Apply offset
        offset = self.ptt_deadline_offset_days or 0
        return ref_date + timedelta(days=offset)

    def action_mark_na(self):
        """Mark subtask as Not Applicable."""
        self.ensure_one()
        self.ptt_marked_na = True
        return True

    def action_unmark_na(self):
        """Remove N/A marking from subtask."""
        self.ensure_one()
        self.ptt_marked_na = False
        return True

    def action_toggle_complete(self):
        """Toggle task completion status (for inline checkbox).

        Uses Odoo 19 native state field:
        - If currently closed (is_closed=True), move to '01_in_progress'
        - If currently open, move to '1_done'
        """
        self.ensure_one()

        if self.is_closed:
            # Currently complete - move back to In Progress
            self.state = '01_in_progress'
        else:
            # Currently incomplete - mark as Done
            self.state = '1_done'

        return True
