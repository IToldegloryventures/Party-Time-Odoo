from odoo import models, api
from datetime import datetime


class AccountMove(models.Model):
    """Inherit Account Move to trigger dashboard KPI updates.
    
    NOTE: This only reads standard Odoo fields - does not modify accounting setup.
    Compatible with 3rd party finance/accounting implementations.
    """
    _inherit = "account.move"
    
    def write(self, vals):
        """Override write to trigger dashboard KPI update when invoices/bills change."""
        result = super().write(vals)
        
        # Trigger dashboard widget KPI update if relevant fields changed
        if any(field in vals for field in ['move_type', 'payment_state', 'state', 'amount_residual']):
            self._trigger_dashboard_kpi_update()
            # Trigger sales rep KPI update if invoice_user_id changed (for customer invoices)
            if 'invoice_user_id' in vals and self.move_type == 'out_invoice':
                self._trigger_sales_rep_kpi_update()
        
        # Trigger CRM Lead Actual Margin recalculation when vendor bills change
        # (vendor bills affect margin calculation via analytic_distribution)
        if self.move_type in ['in_invoice', 'in_refund'] and 'state' in vals and vals['state'] == 'posted':
            self._trigger_crm_lead_margin_update()
        
        return result
    
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to trigger dashboard KPI update when invoices/bills are created."""
        records = super().create(vals_list)
        
        # Trigger dashboard widget KPI update
        self._trigger_dashboard_kpi_update()
        # Trigger sales rep KPI updates for assigned users (customer invoices only)
        for record in records:
            if record.move_type == 'out_invoice' and record.invoice_user_id:
                self._trigger_sales_rep_kpi_update(record.invoice_user_id.id)
            # Trigger CRM Lead Actual Margin recalculation when vendor bills are posted
            if record.move_type in ['in_invoice', 'in_refund'] and record.state == 'posted':
                record._trigger_crm_lead_margin_update()
        
        return records
    
    def _trigger_dashboard_kpi_update(self):
        """Update dashboard widget to trigger KPI recalculation."""
        widget = self.env['ptt.dashboard.widget'].search([], limit=1)
        if widget:
            widget.write({'last_kpi_update': datetime.now()})
    
    def _trigger_sales_rep_kpi_update(self, user_id=None):
        """Update sales rep to trigger KPI recalculation."""
        user_id = user_id or self.invoice_user_id.id if self.invoice_user_id else None
        if user_id:
            sales_rep = self.env['ptt.sales.rep'].search([('user_id', '=', user_id)], limit=1)
            if sales_rep:
                sales_rep.write({'last_kpi_update': datetime.now()})
    
    def _trigger_crm_lead_margin_update(self):
        """Trigger CRM Lead Actual Margin recalculation when vendor bills change.
        
        This finds CRM Leads linked to vendor bills via:
        Vendor Bill → Analytic Account → Project → Sale Order → CRM Lead
        """
        # Only process vendor bills (in_invoice or in_refund)
        if self.move_type not in ['in_invoice', 'in_refund']:
            return
        
        # Get analytic account IDs from bill lines using distribution_analytic_account_ids
        # (computed field from analytic.mixin that extracts account IDs from JSON)
        analytic_account_ids = []
        for line in self.line_ids:
            if hasattr(line, 'distribution_analytic_account_ids') and line.distribution_analytic_account_ids:
                analytic_account_ids.extend(line.distribution_analytic_account_ids.ids)
        
        # Remove duplicates
        analytic_account_ids = list(set(analytic_account_ids))
        
        if not analytic_account_ids:
            return
        
        # Find projects linked to these analytic accounts
        projects = self.env['project.project'].search([
            ('account_id', 'in', analytic_account_ids)
        ])
        
        if not projects:
            return
        
        # Find sale orders linked to these projects
        sale_orders = self.env['sale.order'].search([
            ('project_id', 'in', projects.ids)
        ])
        
        if not sale_orders:
            return
        
        # Find CRM Leads linked to these sale orders
        # Note: order_ids field comes from sale_crm module
        Lead = self.env["crm.lead"]
        if "order_ids" not in Lead._fields:
            return
        crm_leads = Lead.search([("order_ids", "in", sale_orders.ids)])
        
        if crm_leads:
            # Trigger recalculation by marking dependency fields as modified
            # This will cause Odoo to recompute the stored computed fields
            # Official Odoo 19 pattern: use .modified() to trigger recomputation
            crm_leads.modified(['order_ids'])

