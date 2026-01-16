from odoo import models, fields, api


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
        
        return records
    
    def _trigger_dashboard_kpi_update(self):
        """Update dashboard widget to trigger KPI recalculation."""
        widget = self.env['ptt.dashboard.widget'].search([], limit=1)
        if widget:
            widget.write({'last_kpi_update': fields.Datetime.now()})
    
    def _trigger_sales_rep_kpi_update(self, user_id=None):
        """Update sales rep to trigger KPI recalculation."""
        user_id = user_id or self.invoice_user_id.id if self.invoice_user_id else None
        if user_id:
            sales_rep = self.env['ptt.sales.rep'].search([('user_id', '=', user_id)], limit=1)
            if sales_rep:
                sales_rep.write({'last_kpi_update': fields.Datetime.now()})

