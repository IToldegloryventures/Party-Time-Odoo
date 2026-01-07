from odoo import models, fields, api
from datetime import timedelta


class PttSalesRep(models.Model):
    _name = "ptt.sales.rep"
    _description = "PTT Sales Representative"
    _rec_name = "name"
    
    user_id = fields.Many2one("res.users", string="User", required=True, ondelete="cascade")
    name = fields.Char(related="user_id.name", store=True, readonly=True)
    active = fields.Boolean(default=True)
    show_in_dashboard = fields.Boolean(default=True, string="Show in Dashboard Tabs")
    color = fields.Integer(string="Color Index", default=0)
    
    # Trigger field for auto-updating KPIs when related data changes
    last_kpi_update = fields.Datetime(
        string="Last KPI Update",
        default=fields.Datetime.now,
        help="Updated to trigger KPI recalculation when related data changes."
    )
    
    # Computed KPIs (per rep)
    leads_count = fields.Integer(compute="_compute_kpis", string="Leads to Contact", store=True)
    quotes_count = fields.Integer(compute="_compute_kpis", string="Quotes Awaiting Approval", store=True)
    events_count = fields.Integer(compute="_compute_kpis", string="Events This Week", store=True)
    outstanding_amount = fields.Monetary(
        compute="_compute_kpis",
        string="Outstanding Payments",
        currency_field="currency_id",
        store=True
    )
    currency_id = fields.Many2one(
        "res.currency",
        default=lambda self: self.env.company.currency_id,
        ondelete="restrict"
    )
    
    @api.depends("user_id", "last_kpi_update")
    def _compute_kpis(self):
        """Compute KPIs for each sales rep.
        
        Note: Only depends on user_id because KPIs are computed from related models:
        - crm.lead (leads_count) - filtered by user_id
        - sale.order (quotes_count) - filtered by user_id
        - project.project (events_count) - filtered by user_id
        - account.move (outstanding_amount) - filtered by invoice_user_id
        
        These will recalculate when user_id changes or when dashboard is refreshed.
        For real-time updates, consider adding dependencies on related model fields.
        """
        for rep in self:
            if not rep.user_id:
                rep.leads_count = 0
                rep.quotes_count = 0
                rep.events_count = 0
                rep.outstanding_amount = 0.0
                continue
            
            # Filter by user_id for all queries
            rep.leads_count = self.env["crm.lead"].search_count([
                ("user_id", "=", rep.user_id.id),
                ("type", "=", "lead"),
                ("stage_id.name", "in", ["New", "Qualified"])
            ])
            
            rep.quotes_count = self.env["sale.order"].search_count([
                ("user_id", "=", rep.user_id.id),
                ("state", "in", ["draft", "sent"])
            ])
            
            # Events this week - using x_event_date from ptt_business_core
            today = fields.Date.context_today(self)
            week_start = today - timedelta(days=today.weekday())
            week_end = week_start + timedelta(days=6)
            rep.events_count = self.env["project.project"].search_count([
                ("user_id", "=", rep.user_id.id),
                ("x_event_date", ">=", week_start),
                ("x_event_date", "<=", week_end)
            ])
            
            # Outstanding payments
            invoices = self.env["account.move"].search([
                ("move_type", "=", "out_invoice"),
                ("invoice_user_id", "=", rep.user_id.id),
                ("payment_state", "in", ["not_paid", "partial"])
            ])
            rep.outstanding_amount = sum(invoices.mapped("amount_residual"))
    
    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        """Override to enforce access control: non-managers only see their own rep record."""
        # Non-managers only see their own rep record
        if not self.env.user.has_group('sales_team.group_sale_manager'):
            domain = domain or []
            domain.append(('user_id', '=', self.env.user.id))
        return super().search_read(domain, fields, offset, limit, order)

