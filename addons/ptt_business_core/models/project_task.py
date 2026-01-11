from odoo import models, fields, api, _
from datetime import date


class ProjectTask(models.Model):
    _inherit = "project.task"

    # === RELATED FIELDS FOR PROJECT/EVENT CONTEXT ===
    # These provide easy access to project event details on tasks
    
    x_project_event_id = fields.Char(
        string="Event ID",
        related="project_id.x_event_id",
        readonly=True,
        help="Event ID from the related project.",
    )
    
    x_project_event_name = fields.Char(
        string="Event Name",
        related="project_id.x_event_name",
        readonly=True,
        help="Event name from the related project.",
    )
    
    x_project_event_date = fields.Date(
        string="Event Date",
        related="project_id.x_event_date",
        readonly=True,
        help="Event date from the related project.",
    )
    
    x_project_event_time = fields.Char(
        string="Event Time",
        related="project_id.x_event_time",
        readonly=True,
        help="Event time from the related project.",
    )
    
    x_project_event_type = fields.Selection(
        string="Event Type",
        related="project_id.x_event_type",
        readonly=True,
        help="Event type from the related project.",
    )
    
    x_project_venue = fields.Char(
        string="Venue",
        related="project_id.x_venue_name",
        readonly=True,
        help="Venue name from the related project.",
    )
    
    x_project_client_name = fields.Char(
        string="Client Name",
        related="project_id.partner_id.name",
        readonly=True,
        help="Client name from the related project.",
    )
    
    x_project_guest_count = fields.Integer(
        string="Guest Count",
        related="project_id.x_guest_count",
        readonly=True,
        help="Guest count from the related project.",
    )
    
    x_project_crm_lead_id = fields.Many2one(
        "crm.lead",
        string="Source Opportunity",
        related="project_id.x_crm_lead_id",
        readonly=True,
        help="Source CRM opportunity from the related project.",
    )
    
    x_project_sales_rep_id = fields.Many2one(
        "res.users",
        string="Sales Rep",
        related="project_id.x_sales_rep_id",
        readonly=True,
        help="Sales representative from the related project.",
    )

    # === COMPUTED FIELDS ===
    
    x_is_event_task = fields.Boolean(
        string="Is Event Task",
        compute="_compute_is_event_task",
        help="True if this task is part of an event project (has CRM lead).",
    )

    @api.depends("project_id.x_crm_lead_id")
    def _compute_is_event_task(self):
        """Determine if this task belongs to an event project."""
        for task in self:
            task.x_is_event_task = bool(task.project_id and task.project_id.x_crm_lead_id)

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
    
    def action_view_crm_lead(self):
        """Open the source CRM opportunity."""
        self.ensure_one()
        if not self.project_id or not self.project_id.x_crm_lead_id:
            return False
        return {
            "type": "ir.actions.act_window",
            "name": _("Source Opportunity"),
            "res_model": "crm.lead",
            "res_id": self.project_id.x_crm_lead_id.id,
            "view_mode": "form",
            "target": "current",
        }
    
    def action_view_sale_order(self):
        """Open the related Sales Order (via CRM lead)."""
        self.ensure_one()
        if not self.project_id or not self.project_id.x_crm_lead_id:
            return False
        orders = self.project_id.x_crm_lead_id.order_ids
        if not orders:
            return False
        if len(orders) == 1:
            return {
                "type": "ir.actions.act_window",
                "name": _("Sales Order"),
                "res_model": "sale.order",
                "res_id": orders.id,
                "view_mode": "form",
                "target": "current",
            }
        return {
            "type": "ir.actions.act_window",
            "name": _("Sales Orders"),
            "res_model": "sale.order",
            "view_mode": "tree,form",
            "domain": [("id", "in", orders.ids)],
            "target": "current",
        }
