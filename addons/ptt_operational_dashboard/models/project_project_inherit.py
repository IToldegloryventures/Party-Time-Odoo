from odoo import models, api
from datetime import datetime


class ProjectProject(models.Model):
    """Inherit Project to trigger dashboard KPI updates.
    
    Note: PTT event fields (ptt_event_date, ptt_crm_lead_id) are defined in
    ptt_business_core.models.project_project - do NOT redefine them here.
    """
    _inherit = "project.project"
    
    def write(self, vals):
        """Override write to trigger dashboard KPI update when projects change."""
        result = super().write(vals)
        
        # Trigger dashboard widget KPI update if relevant fields changed
        if any(field in vals for field in ['ptt_event_date', 'user_id', 'account_id']):
            self._trigger_dashboard_kpi_update()
            # Trigger sales rep KPI update if user_id changed
            if 'user_id' in vals:
                self._trigger_sales_rep_kpi_update()
        
        return result
    
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to trigger dashboard KPI update when projects are created."""
        records = super().create(vals_list)
        
        # Trigger dashboard widget KPI update
        self._trigger_dashboard_kpi_update()
        # Trigger sales rep KPI updates for assigned users
        for record in records:
            if record.user_id:
                self._trigger_sales_rep_kpi_update(record.user_id.id)
        
        return records
    
    def _trigger_dashboard_kpi_update(self):
        """Update dashboard widget to trigger KPI recalculation."""
        widget = self.env['ptt.dashboard.widget'].search([], limit=1)
        if widget:
            widget.write({'last_kpi_update': datetime.now()})
    
    def _trigger_sales_rep_kpi_update(self, user_id=None):
        """Update sales rep to trigger KPI recalculation."""
        user_id = user_id or self.user_id.id if self.user_id else None
        if user_id:
            sales_rep = self.env['ptt.sales.rep'].search([('user_id', '=', user_id)], limit=1)
            if sales_rep:
                sales_rep.write({'last_kpi_update': datetime.now()})

