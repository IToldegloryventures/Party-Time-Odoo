# Part of Party Time Texas Event Management System
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
"""
Enhanced Project model for Party Time Texas event management.

NOTE: Project templates are now native Odoo project.project records with is_template=True.
Templates are defined in ptt_business_core/data/project_template.xml:
- project_template_corporate
- project_template_wedding  
- project_template_social

When a Sale Order with Event Kickoff product is confirmed, Odoo's native template
copying mechanism creates the project with all tasks and subtasks from the template.
"""

from odoo import models, fields, api, _

from odoo.addons.ptt_business_core.constants import EVENT_STATUS


class ProjectProject(models.Model):
    """Enhanced Project for Event Management"""
    _inherit = 'project.project'

    # Stakeholder Management (Simple Contact Directory)
    stakeholder_ids = fields.One2many(
        'project.stakeholder',
        'project_id',
        string="Stakeholders",
        help="Contact directory for this event - clients, vendors, key contacts"
    )
    
    # Simple Stakeholder Counts for smart buttons
    vendor_count = fields.Integer(
        string="Vendors",
        compute='_compute_stakeholder_counts',
        store=True
    )
    
    client_count = fields.Integer(
        string="Clients",
        compute='_compute_stakeholder_counts',
        store=True
    )
    
    # Event Status
    event_status = fields.Selection(
        selection=EVENT_STATUS,
        string="Event Status",
        default='planning'
    )
    
    # NOTE: Event type is defined in ptt_enhanced_sales/models/project_project.py:
    # - ptt_event_type (Selection): Related to CRM Lead ptt_event_type field.
    # Values: corporate, social, wedding. Do not add duplicate definitions here.
    
    @api.depends('stakeholder_ids.is_vendor', 'stakeholder_ids.is_client')
    def _compute_stakeholder_counts(self):
        """Compute stakeholder counts by type."""
        for project in self:
            project.vendor_count = len(project.stakeholder_ids.filtered('is_vendor'))
            project.client_count = len(project.stakeholder_ids.filtered('is_client'))
    
    def action_view_stakeholders(self):
        """Open list view of all stakeholders for this project."""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Event Contacts',
            'res_model': 'project.stakeholder',
            'view_mode': 'list,form',
            'domain': [('project_id', '=', self.id)],
            'context': {'default_project_id': self.id},
            'target': 'current',
        }
    
    def action_view_crm_lead(self):
        """Open the source CRM opportunity for this project.
        
        Returns:
            dict: Action to open the CRM lead form.
        """
        self.ensure_one()
        if not self.ptt_crm_lead_id:
            return {'type': 'ir.actions.act_window_close'}
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Source Opportunity'),
            'res_model': 'crm.lead',
            'view_mode': 'form',
            'res_id': self.ptt_crm_lead_id.id,
            'target': 'current',
        }
    
    def action_view_sale_order(self):
        """Open the source sale order for this project.
        
        Returns:
            dict: Action to open the sale order form.
        """
        self.ensure_one()
        if not self.sale_order_id:
            return {'type': 'ir.actions.act_window_close'}
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Sale Order'),
            'res_model': 'sale.order',
            'view_mode': 'form',
            'res_id': self.sale_order_id.id,
            'target': 'current',
        }
    
    def action_view_vendors(self):
        """Open list view of vendor stakeholders only.
        
        Returns:
            dict: Action to open vendor stakeholder list.
        """
        return {
            'type': 'ir.actions.act_window',
            'name': 'Event Vendors',
            'res_model': 'project.stakeholder',
            'view_mode': 'list,form',
            'domain': [('project_id', '=', self.id), ('is_vendor', '=', True)],
            'context': {'default_project_id': self.id, 'default_is_vendor': True},
            'target': 'current',
        }
    
    def action_view_clients(self):
        """Open list view of client stakeholders only."""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Event Clients',
            'res_model': 'project.stakeholder',
            'view_mode': 'list,form',
            'domain': [('project_id', '=', self.id), ('is_client', '=', True)],
            'context': {'default_project_id': self.id, 'default_is_client': True},
            'target': 'current',
        }

    # =========================================================================
    # COMPUTED FIELDS FOR DASHBOARD
    # =========================================================================
    ptt_task_progress = fields.Float(
        string="Task Progress",
        compute="_compute_task_progress",
        store=True,
        help="Overall task completion percentage"
    )

    ptt_task_summary = fields.Char(
        string="Task Summary",
        compute="_compute_task_progress",
        store=True,
    )

    ptt_overdue_task_count = fields.Integer(
        string="Overdue Tasks",
        compute="_compute_overdue_tasks",
        help="Number of tasks past their deadline"
    )

    ptt_days_until_event = fields.Integer(
        string="Days Until Event",
        compute="_compute_days_until_event",
        help="Days remaining until the event date"
    )

    # =========================================================================
    # COMPUTED METHODS FOR DASHBOARD
    # =========================================================================
    @api.depends('task_ids', 'task_ids.state')
    def _compute_task_progress(self):
        """Compute overall task completion progress.

        Uses Odoo 19 native `is_closed` field which checks if state is in CLOSED_STATES.
        """
        for project in self:
            # Only count parent tasks (not subtasks)
            tasks = project.task_ids.filtered(lambda t: not t.parent_id)
            if not tasks:
                project.ptt_task_progress = 0.0
                project.ptt_task_summary = "No tasks"
                continue

            total = len(tasks)
            complete = len(tasks.filtered(lambda t: t.is_closed))

            project.ptt_task_progress = (complete / total * 100) if total else 0.0
            project.ptt_task_summary = f"{complete}/{total} tasks complete"

    @api.depends('task_ids', 'task_ids.date_deadline', 'task_ids.state')
    def _compute_overdue_tasks(self):
        """Count overdue tasks using Odoo 19 state field."""
        today = fields.Date.today()
        for project in self:
            overdue = project.task_ids.filtered(
                lambda t: t.date_deadline
                and (t.date_deadline.date() if hasattr(t.date_deadline, 'date') else t.date_deadline) < today
                and not t.is_closed
            )
            project.ptt_overdue_task_count = len(overdue)

    @api.depends('ptt_event_date')
    def _compute_days_until_event(self):
        """Compute days until event."""
        today = fields.Date.today()
        for project in self:
            if project.ptt_event_date:
                delta = project.ptt_event_date - today
                project.ptt_days_until_event = delta.days
            else:
                project.ptt_days_until_event = 0

    # =========================================================================
    # DEADLINE RECALCULATION
    # =========================================================================
    def action_recalculate_deadlines(self):
        """Manually trigger deadline recalculation for all tasks.

        Called from a button on the project form or programmatically
        when sale order or event date changes.
        """
        for project in self:
            project._recalculate_task_deadlines()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Deadlines Updated"),
                'message': _("Task deadlines have been recalculated based on the event date."),
                'type': 'success',
                'sticky': False,
            }
        }

    def _recalculate_task_deadlines(self):
        """Recalculate deadlines for all tasks based on Sale Order dates.

        Uses the linked sale_order_id to get:
        - date_order: for tasks with reference='confirmation'
        - event_date: for tasks with reference='event'
        """
        self.ensure_one()

        sale_order = self.sale_order_id
        if not sale_order:
            return

        # Get all tasks with deadline configuration
        tasks_to_update = self.task_ids.filtered(
            lambda t: t.ptt_deadline_reference and t.ptt_deadline_offset_days is not False
        )

        for task in tasks_to_update:
            new_deadline = task._calculate_deadline_from_sale_order(sale_order)
            if new_deadline:
                task.write({
                    'date_deadline': new_deadline,
                    'ptt_deadline_auto_calculated': True,
                })

        # Also update subtasks that inherit from parent
        for task in tasks_to_update:
            for subtask in task.child_ids:
                if subtask.ptt_deadline_reference and subtask.ptt_deadline_offset_days is not False:
                    new_deadline = subtask._calculate_deadline_from_sale_order(sale_order)
                    if new_deadline:
                        subtask.write({
                            'date_deadline': new_deadline,
                            'ptt_deadline_auto_calculated': True,
                        })

    # =========================================================================
    # TASK DASHBOARD ACTION
    # =========================================================================
    def action_open_task_dashboard(self):
        """Open the single-page task dashboard for this project.

        Shows all tasks and subtasks with inline completion checkboxes.
        """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Task Dashboard - %s', self.name),
            'res_model': 'project.task',
            'view_mode': 'tree,form',
            'domain': [('project_id', '=', self.id)],
            'context': {
                'default_project_id': self.id,
                'search_default_group_by_parent': True,
                'ptt_task_dashboard': True,
            },
            'target': 'current',
        }

    def action_view_overdue_tasks(self):
        """View only overdue tasks for this project."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Overdue Tasks'),
            'res_model': 'project.task',
            'view_mode': 'tree,form',
            'domain': [
                ('project_id', '=', self.id),
                ('ptt_is_overdue', '=', True),
            ],
            'context': {'default_project_id': self.id},
            'target': 'current',
        }