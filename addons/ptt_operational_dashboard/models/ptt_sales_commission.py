from odoo import models, fields, api
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class PttSalesCommission(models.Model):
    """Sales Commission Report - Monthly commission tracking per sales rep."""
    _name = "ptt.sales.commission"
    _description = "PTT Sales Commission Report"
    _order = "report_month desc, sales_rep_id"
    _rec_name = "display_name"

    # === IDENTIFICATION ===
    sales_rep_id = fields.Many2one(
        "ptt.sales.rep",
        string="Sales Representative",
        required=True,
        index=True,
        ondelete="restrict",
        help="Sales rep this commission report is for."
    )
    x_sales_rep_name = fields.Char(
        related="sales_rep_id.name",
        string="Sales Rep Name",
        store=True,
        readonly=True
    )
    
    # === DATE FILTERING ===
    report_month = fields.Date(
        string="Report Month",
        required=True,
        default=lambda self: fields.Date.today().replace(day=1),  # Default to first day of current month
        index=True,
        help="Month this commission report is for (defaults to current month)."
    )
    month_start = fields.Date(
        compute="_compute_month_dates",
        store=True,
        string="Month Start",
        help="First day of the report month."
    )
    month_end = fields.Date(
        compute="_compute_month_dates",
        store=True,
        string="Month End",
        help="Last day of the report month."
    )
    
    # === REVENUE ===
    total_revenue = fields.Monetary(
        string="Total Revenue",
        compute="_compute_commission_data",
        currency_field="currency_id",
        store=True,
        help="Total revenue from confirmed Sale Orders for this rep in this month."
    )
    
    # === MARGINS ===
    total_margin = fields.Monetary(
        string="Total Margin",
        compute="_compute_commission_data",
        currency_field="currency_id",
        store=True,
        help="Total margin (revenue - costs) for this rep in this month."
    )
    margin_percent = fields.Float(
        string="Margin %",
        compute="_compute_commission_data",
        store=True,
        digits=(16, 2),
        help="Average margin percentage for this rep in this month."
    )
    
    # === COMMISSION ===
    commission_amount = fields.Monetary(
        string="Commission Amount",
        compute="_compute_commission_data",
        currency_field="currency_id",
        store=True,
        help="Calculated commission amount based on business rules (to be configured)."
    )
    commission_percent = fields.Float(
        string="Commission %",
        compute="_compute_commission_data",
        store=True,
        digits=(16, 2),
        help="Commission percentage applied (to be configured based on business rules)."
    )
    
    # === SUPPORTING DATA ===
    currency_id = fields.Many2one(
        "res.currency",
        default=lambda self: self.env.company.currency_id,
        required=True,
        ondelete="restrict"
    )
    
    # === DISPLAY ===
    display_name = fields.Char(
        compute="_compute_display_name",
        store=True,
        string="Display Name"
    )
    
    @api.depends("report_month")
    def _compute_month_dates(self):
        """Calculate month start and end dates from report_month."""
        for rec in self:
            if rec.report_month:
                # Month start is the first day of the month
                rec.month_start = rec.report_month.replace(day=1)
                # Month end is the last day of the month
                next_month = rec.report_month + relativedelta(months=1)
                rec.month_end = next_month - timedelta(days=1)
            else:
                rec.month_start = False
                rec.month_end = False
    
    @api.depends("sales_rep_id", "report_month", "month_start", "month_end")
    def _compute_commission_data(self):
        """Compute revenue, margin, and commission for the sales rep in the specified month.
        
        Commission Plan Implementation (Effective July 1, 2025):
        - Only calculates for "Completed Events" (invoiced, delivered, fully collected, all vendor bills paid)
        - Standard Sales: Tiered commission based on Gross Margin %
        - OSS Sales: 50% Year 1, 25% Year 2, then Standard Sales structure
        - Commission splits handled per rep based on their allocated revenue/costs
        """
        for rec in self:
            if not rec.sales_rep_id or not rec.month_start or not rec.month_end:
                rec.total_revenue = 0.0
                rec.total_margin = 0.0
                rec.margin_percent = 0.0
                rec.commission_amount = 0.0
                rec.commission_percent = 0.0
                continue
            
            user_id = rec.sales_rep_id.user_id.id
            
            # Get COMPLETED EVENTS only (invoiced, delivered, fully collected, all vendor bills paid)
            # For now, we'll use confirmed sale orders - TODO: Add "Completed Event" status tracking
            confirmed_orders = self.env["sale.order"].search([
                ("user_id", "=", user_id),
                ("state", "=", "sale"),  # Confirmed orders
                ("date_order", ">=", rec.month_start),
                ("date_order", "<=", rec.month_end)
            ])
            
            # Filter to only "Completed Events" - events where:
            # 1. Invoiced (has invoice)
            # 2. Delivered (project state = done or similar)
            # 3. Fully collected (all invoices paid)
            # 4. All vendor bills paid (no outstanding vendor bills)
            completed_orders = []
            cumulative_revenue = 0.0
            cumulative_costs = 0.0
            
            for order in confirmed_orders:
                # Check if event is completed
                is_completed = self._is_completed_event(order)
                if not is_completed:
                    continue
                
                completed_orders.append(order)
                
                # Get revenue for this rep (considering commission splits)
                # TODO: Apply commission split percentage when split tracking is implemented
                # For now, assume 100% to this rep (user_id matches)
                rep_revenue_share = 1.0  # Will be replaced with actual split percentage
                rep_revenue = order.amount_total * rep_revenue_share
                cumulative_revenue += rep_revenue
                
                # Get costs allocated to this rep
                project = order.project_id
                if project:
                    rep_costs_share = rep_revenue_share  # Same split for costs
                    project_costs = self._get_project_costs(project, rec.month_start, rec.month_end)
                    rep_costs = project_costs * rep_costs_share
                    cumulative_costs += rep_costs
            
            rec.total_revenue = cumulative_revenue
            
            # Calculate margin
            rec.total_margin = cumulative_revenue - cumulative_costs
            if cumulative_revenue > 0:
                rec.margin_percent = (rec.total_margin / cumulative_revenue) * 100
            else:
                rec.margin_percent = 0.0
            
            # Calculate commission based on commission plan
            rec.commission_amount, rec.commission_percent = self._calculate_commission(
                completed_orders, cumulative_revenue, cumulative_costs, rec.margin_percent, user_id
            )
    
    def _is_completed_event(self, sale_order):
        """Check if sale order represents a 'Completed Event'.
        
        Completed Event criteria:
        1. Has invoice(s)
        2. All invoices are posted and fully paid
        3. Project is delivered (if exists)
        4. All vendor bills are paid (if project exists)
        """
        # Check if has invoices
        invoices = sale_order.invoice_ids.filtered(lambda inv: inv.move_type == 'out_invoice')
        if not invoices:
            return False
        
        # Check if all invoices are posted and fully paid
        for invoice in invoices:
            if invoice.state != 'posted':
                return False
            if invoice.payment_state not in ['paid', 'in_payment']:
                return False
        
        # Check if project exists and vendor bills are paid
        project = sale_order.project_id
        if project:
            # Check if all vendor bills are paid
            # Get vendor bills linked to this project via analytic_distribution (standard Odoo pattern)
            if project.account_id:
                vendor_bill_lines = self.env["account.move.line"].search([
                    ("move_id.move_type", "in", ["in_invoice", "in_refund"]),
                    ("move_id.state", "=", "posted"),
                    ("analytic_distribution", "in", [str(project.account_id.id)])
                ])
                vendor_bills = vendor_bill_lines.mapped("move_id")
                for bill in vendor_bills:
                    if bill.payment_state not in ['paid', 'in_payment']:
                        return False
        
        return True
    
    def _get_project_costs(self, project, month_start, month_end):
        """Get project costs (vendor bills) for the specified month."""
        total_costs = 0.0
        
        if project.account_id:
            # PRIMARY: Use accounting data (vendor bills via analytic_distribution)
            vendor_bill_lines = self.env["account.move.line"].search([
                ("move_id.move_type", "in", ["in_invoice", "in_refund"]),
                ("move_id.state", "=", "posted"),
                ("analytic_distribution", "in", [str(project.account_id.id)]),
                ("move_id.date", ">=", month_start),
                ("move_id.date", "<=", month_end)
            ])
            vendor_bills = vendor_bill_lines.mapped("move_id")
            for bill in vendor_bills:
                if bill.move_type == "in_invoice":
                    total_costs += bill.amount_total
                elif bill.move_type == "in_refund":
                    total_costs -= bill.amount_total
        else:
            # FALLBACK: Use project fields
            total_costs = project.x_actual_total_vendor_costs or 0.0
        
        return total_costs
    
    def _calculate_commission(self, completed_orders, revenue, costs, margin_percent, user_id):
        """Calculate commission based on Party Time Texas Commission Plan.
        
        Standard Sales Commission Structure (Tiered by GM%):
        - <26%: 0%
        - 26% to <30%: 1%
        - 30% to <35%: 2%
        - 35% to <36%: 2.5%
        - 36% to <37%: 3%
        - 37% to <38%: 3.5%
        - 38% and above: 4%
        
        OSS Commission Structure (for New Outside Clients):
        - Year 1: 50% of split commission
        - Year 2: 25% of split commission
        - After Year 2: Standard Sales structure
        
        Returns: (commission_amount, commission_percent)
        """
        if revenue <= 0:
            return (0.0, 0.0)
        
        # Determine if any orders are from New Outside Clients (OSS)
        # TODO: Check OSS status when OSS tracking fields are added
        # For now, we'll calculate based on Standard Sales structure
        
        # Apply Standard Sales tiered commission structure
        commission_rate = self._get_standard_commission_rate(margin_percent)
        
        # Calculate commission amount
        commission_amount = revenue * (commission_rate / 100.0)
        
        return (commission_amount, commission_rate)
    
    def _get_standard_commission_rate(self, margin_percent):
        """Get commission rate based on Gross Margin % (Standard Sales structure).
        
        Commission Plan Tiered Rates:
        - <26%: 0%
        - 26% to <30%: 1%
        - 30% to <35%: 2%
        - 35% to <36%: 2.5%
        - 36% to <37%: 3%
        - 37% to <38%: 3.5%
        - 38% and above: 4%
        """
        if margin_percent < 26.0:
            return 0.0
        elif margin_percent < 30.0:
            return 1.0
        elif margin_percent < 35.0:
            return 2.0
        elif margin_percent < 36.0:
            return 2.5
        elif margin_percent < 37.0:
            return 3.0
        elif margin_percent < 38.0:
            return 3.5
        else:  # 38% and above
            return 4.0
    
    def _is_new_outside_client(self, partner_id, order_date):
        """Check if partner is a 'New Outside Client' (not booked in 24 months).
        
        New Outside Client: Has not contracted within past 24 months.
        """
        if not partner_id:
            return False
        
        # Get commercial partner (parent company if exists)
        partner = self.env["res.partner"].browse(partner_id)
        commercial_partner = partner.commercial_partner_id
        
        # Check for sale orders in last 24 months (excluding current order)
        twenty_four_months_ago = order_date - relativedelta(months=24)
        previous_orders = self.env["sale.order"].search([
            ("partner_id.commercial_partner_id", "=", commercial_partner.id),
            ("state", "=", "sale"),
            ("date_order", ">=", twenty_four_months_ago),
            ("date_order", "<", order_date)
        ], limit=1)
        
        # If no orders in last 24 months, it's a New Outside Client
        return not bool(previous_orders)
    
    @api.depends("x_sales_rep_name", "report_month")
    def _compute_display_name(self):
        """Generate display name: 'Sales Rep Name - Month Year'."""
        for rec in self:
            if rec.x_sales_rep_name and rec.report_month:
                month_name = rec.report_month.strftime("%B %Y")
                rec.display_name = f"{rec.x_sales_rep_name} - {month_name}"
            else:
                rec.display_name = "New Commission Report"
    
    @api.model
    def create_monthly_reports(self, month_date=None):
        """Create commission reports for all active sales reps for a given month.
        
        Args:
            month_date: Date object for the month (defaults to current month)
        """
        if not month_date:
            month_date = fields.Date.today().replace(day=1)
        
        # Get all active sales reps
        sales_reps = self.env["ptt.sales.rep"].search([("active", "=", True)])
        
        reports_created = []
        for rep in sales_reps:
            # Check if report already exists
            existing = self.search([
                ("sales_rep_id", "=", rep.id),
                ("report_month", "=", month_date)
            ])
            
            if not existing:
                report = self.create({
                    "sales_rep_id": rep.id,
                    "report_month": month_date
                })
                reports_created.append(report.id)
        
        return self.browse(reports_created)

