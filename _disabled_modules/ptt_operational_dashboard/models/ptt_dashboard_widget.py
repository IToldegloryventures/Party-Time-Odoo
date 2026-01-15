from odoo import models, fields, api
from datetime import timedelta


class PttDashboardWidget(models.Model):
    _name = "ptt.dashboard.widget"
    _description = "PTT Dashboard Widget (Singleton)"
    _rec_name = "name"
    
    name = fields.Char(default="PTT Dashboard", readonly=True)
    
    @api.model
    def _get_or_create_widget(self):
        """Get or create the singleton dashboard widget."""
        widget = self.search([], limit=1)
        if not widget:
            widget = self.create({'name': 'PTT Dashboard'})
        return widget
    
    # Trigger field for auto-updating KPIs when related data changes
    # This field gets updated via automation/cron to trigger recalculation
    last_kpi_update = fields.Datetime(
        string="Last KPI Update",
        default=fields.Datetime.now,
        help="Updated to trigger KPI recalculation when related data changes."
    )
    
    # Company-wide KPIs
    total_leads = fields.Integer(compute="_compute_overview_kpis", store=True)
    total_quotes = fields.Integer(compute="_compute_overview_kpis", store=True)
    total_events_week = fields.Integer(compute="_compute_overview_kpis", store=True)
    total_outstanding = fields.Monetary(
        compute="_compute_overview_kpis",
        currency_field="currency_id",
        store=True
    )
    vendor_compliance_issues = fields.Integer(compute="_compute_overview_kpis", store=True)
    currency_id = fields.Many2one(
        "res.currency",
        default=lambda self: self.env.company.currency_id,
        ondelete="restrict"
    )
    
    @api.depends("last_kpi_update")
    def _compute_overview_kpis(self):
        """Compute company-wide KPIs.
        
        Depends on last_kpi_update trigger field which is updated when related data changes.
        Computes from multiple unrelated models:
        - crm.lead (leads)
        - sale.order (quotes, revenue)
        - project.project (events, costs)
        - account.move (outstanding payments, vendor bills)
        
        This method will recalculate when last_kpi_update changes.
        For real-time updates, consider adding a cron job or bus notifications.
        """
        for rec in self:
            # Aggregate across all sales reps
            rec.total_leads = self.env["crm.lead"].search_count([
                ("type", "=", "lead"),
                ("stage_id.name", "in", ["Intake", "Qualification"])
            ])
            
            rec.total_quotes = self.env["sale.order"].search_count([
                ("state", "in", ["draft", "sent"])
            ])
            
            # Events this week - using ptt_event_date from ptt_business_core (project.project inherit)
            today = fields.Date.context_today(self)
            week_start = today - timedelta(days=today.weekday())
            week_end = week_start + timedelta(days=6)
            Project = self.env["project.project"]
            if "ptt_event_date" in Project._fields:
                rec.total_events_week = Project.search_count([
                    ("ptt_event_date", ">=", week_start),
                    ("ptt_event_date", "<=", week_end),
                ])
            else:
                rec.total_events_week = 0
            
            invoices = self.env["account.move"].search([
                ("move_type", "=", "out_invoice"),
                ("payment_state", "in", ["not_paid", "partial"])
            ])
            rec.total_outstanding = sum(invoices.mapped("amount_residual"))
            
            # TODO: Implement vendor compliance logic
            rec.vendor_compliance_issues = 0
    
    # Quick action methods
    def action_new_lead(self):
        """Open form to create new lead."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "New Lead",
            "res_model": "crm.lead",
            "view_mode": "form",
            "target": "current",
            "context": {"default_type": "lead"}
        }
    
    def action_start_quote(self):
        """Open form to create new quote."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "New Quote",
            "res_model": "sale.order",
            "view_mode": "form",
            "target": "current",
            "context": {"default_state": "draft"}
        }
    
    def action_assign_vendor(self):
        """Open vendor list filtered to companies.
        
        Uses native supplier_rank field to identify vendors (supplier_rank > 0 = vendor).
        """
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Assign Vendor",
            "res_model": "res.partner",
            "view_mode": "list,form",
            "target": "current",
            "domain": [("is_company", "=", True), ("supplier_rank", ">", 0)],
        }
    
    def action_record_payment(self):
        """Open form to record payment."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Record Payment",
            "res_model": "account.payment",
            "view_mode": "form",
            "target": "new"
        }
    
    def action_upload_vendor_doc(self):
        """Open form to upload vendor document."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Upload Vendor Document",
            "res_model": "ir.attachment",
            "view_mode": "form",
            "target": "new"
        }
    
    def action_view_event_timeline(self):
        """Open event timeline view."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Event Timeline",
            "res_model": "project.project",
            "view_mode": "kanban,form",
            "target": "current"
        }
    
    def action_view_leads(self):
        """Open leads list/pivot view where users can use standard Odoo export or pivot Excel export."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Leads",
            "res_model": "crm.lead",
            "view_mode": "list,pivot,form",
            "target": "current",
            "domain": [("type", "=", "lead")],
            "context": {"search_default_type": "lead"}
        }
    
    def action_view_leads_current_month(self):
        """Open leads pivot view filtered to current month - can export as Excel."""
        self.ensure_one()
        today = fields.Date.context_today(self)
        month_start = today.replace(day=1)
        if today.month == 12:
            month_end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            month_end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
        return {
            "type": "ir.actions.act_window",
            "name": "Leads - Current Month",
            "res_model": "crm.lead",
            "view_mode": "pivot,list,form",
            "target": "current",
            "domain": [
                ("type", "=", "lead"),
                ("create_date", ">=", month_start.strftime("%Y-%m-%d")),
                ("create_date", "<=", month_end.strftime("%Y-%m-%d 23:59:59"))
            ],
            "context": {
                "search_default_type": "lead",
                "pivot_measures": ["expected_revenue"],
                "pivot_column_groupby": ["create_date:month"],
            }
        }
    
    def action_view_leads_previous_month(self):
        """Open leads pivot view filtered to previous month - can export as Excel."""
        self.ensure_one()
        today = fields.Date.context_today(self)
        if today.month == 1:
            prev_month_start = today.replace(year=today.year - 1, month=12, day=1)
            prev_month_end = today.replace(day=1) - timedelta(days=1)
        else:
            prev_month_start = today.replace(month=today.month - 1, day=1)
            prev_month_end = today.replace(day=1) - timedelta(days=1)
        return {
            "type": "ir.actions.act_window",
            "name": "Leads - Previous Month",
            "res_model": "crm.lead",
            "view_mode": "pivot,list,form",
            "target": "current",
            "domain": [
                ("type", "=", "lead"),
                ("create_date", ">=", prev_month_start.strftime("%Y-%m-%d")),
                ("create_date", "<=", prev_month_end.strftime("%Y-%m-%d 23:59:59"))
            ],
            "context": {
                "search_default_type": "lead",
                "pivot_measures": ["expected_revenue"],
                "pivot_column_groupby": ["create_date:month"],
            }
        }
    
    def action_view_quotes(self):
        """Open quotes list/pivot view where users can use standard Odoo export or pivot Excel export."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Quotes",
            "res_model": "sale.order",
            "view_mode": "list,pivot,form",
            "target": "current",
            "domain": [("state", "in", ["draft", "sent", "sale"])],
        }
    
    def action_view_quotes_current_month(self):
        """Open quotes pivot view filtered to current month - can export as Excel."""
        self.ensure_one()
        today = fields.Date.context_today(self)
        month_start = today.replace(day=1)
        if today.month == 12:
            month_end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            month_end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
        return {
            "type": "ir.actions.act_window",
            "name": "Quotes - Current Month",
            "res_model": "sale.order",
            "view_mode": "pivot,list,form",
            "target": "current",
            "domain": [
                ("state", "in", ["draft", "sent", "sale"]),
                ("date_order", ">=", month_start.strftime("%Y-%m-%d")),
                ("date_order", "<=", month_end.strftime("%Y-%m-%d 23:59:59"))
            ],
            "context": {
                "pivot_measures": ["amount_total"],
                "pivot_column_groupby": ["date_order:month"],
            }
        }
    
    def action_view_quotes_previous_month(self):
        """Open quotes pivot view filtered to previous month - can export as Excel."""
        self.ensure_one()
        today = fields.Date.context_today(self)
        if today.month == 1:
            prev_month_start = today.replace(year=today.year - 1, month=12, day=1)
            prev_month_end = today.replace(day=1) - timedelta(days=1)
        else:
            prev_month_start = today.replace(month=today.month - 1, day=1)
            prev_month_end = today.replace(day=1) - timedelta(days=1)
        return {
            "type": "ir.actions.act_window",
            "name": "Quotes - Previous Month",
            "res_model": "sale.order",
            "view_mode": "pivot,list,form",
            "target": "current",
            "domain": [
                ("state", "in", ["draft", "sent", "sale"]),
                ("date_order", ">=", prev_month_start.strftime("%Y-%m-%d")),
                ("date_order", "<=", prev_month_end.strftime("%Y-%m-%d 23:59:59"))
            ],
            "context": {
                "pivot_measures": ["amount_total"],
                "pivot_column_groupby": ["date_order:month"],
            }
        }
    
    def action_view_events(self):
        """Open events list/pivot view where users can use standard Odoo export or pivot Excel export."""
        self.ensure_one()
        Project = self.env["project.project"]
        if "ptt_event_date" not in Project._fields:
            today = fields.Date.context_today(self)
            return {
                "type": "ir.actions.act_window",
                "name": "Events",
                "res_model": "project.project",
                "view_mode": "list,form",
                "target": "current",
            }
        today = fields.Date.context_today(self)
        return {
            "type": "ir.actions.act_window",
            "name": "Events",
            "res_model": "project.project",
            "view_mode": "list,pivot,form",
            "target": "current",
            "domain": [
                ("ptt_event_date", ">=", today),
                ("ptt_event_date", "<=", today + timedelta(days=30))
            ],
        }
    
    def action_view_events_current_month(self):
        """Open events pivot view filtered to current month - can export as Excel."""
        self.ensure_one()
        Project = self.env["project.project"]
        if "ptt_event_date" not in Project._fields:
            return self.action_view_events()
        today = fields.Date.context_today(self)
        month_start = today.replace(day=1)
        if today.month == 12:
            month_end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            month_end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
        return {
            "type": "ir.actions.act_window",
            "name": "Events - Current Month",
            "res_model": "project.project",
            "view_mode": "pivot,list,form",
            "target": "current",
            "domain": [
                ("ptt_event_date", ">=", month_start.strftime("%Y-%m-%d")),
                ("ptt_event_date", "<=", month_end.strftime("%Y-%m-%d"))
            ],
        }
    
    def action_view_events_previous_month(self):
        """Open events pivot view filtered to previous month - can export as Excel."""
        self.ensure_one()
        Project = self.env["project.project"]
        if "ptt_event_date" not in Project._fields:
            return self.action_view_events()
        today = fields.Date.context_today(self)
        if today.month == 1:
            prev_month_start = today.replace(year=today.year - 1, month=12, day=1)
            prev_month_end = today.replace(day=1) - timedelta(days=1)
        else:
            prev_month_start = today.replace(month=today.month - 1, day=1)
            prev_month_end = today.replace(day=1) - timedelta(days=1)
        return {
            "type": "ir.actions.act_window",
            "name": "Events - Previous Month",
            "res_model": "project.project",
            "view_mode": "pivot,list,form",
            "target": "current",
            "domain": [
                ("ptt_event_date", ">=", prev_month_start.strftime("%Y-%m-%d")),
                ("ptt_event_date", "<=", prev_month_end.strftime("%Y-%m-%d"))
            ],
        }
    
    def action_view_outstanding(self):
        """Open outstanding invoices list/pivot view."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Outstanding Payments",
            "res_model": "account.move",
            "view_mode": "list,pivot,form",
            "target": "current",
            "domain": [
                ("move_type", "=", "out_invoice"),
                ("payment_state", "in", ["not_paid", "partial"])
            ],
            "context": {
                "search_default_not_paid": 1,
                "pivot_measures": ["amount_residual"],
                "pivot_column_groupby": ["invoice_date:month"],
            }
        }
    
    def action_view_vendor_compliance(self):
        """Open vendor compliance issues view.
        
        Uses native supplier_rank field to identify vendors (supplier_rank > 0 = vendor).
        """
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Vendor Compliance Issues",
            "res_model": "res.partner",
            "view_mode": "list,form",
            "target": "current",
            "domain": [("is_company", "=", True), ("supplier_rank", ">", 0)],
            "context": {
                "search_default_compliance_issues": 1,
            }
        }
    

