# Part of Party Time Texas Event Management System
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models
import logging

_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    """Extend sale.order.line to include event details when creating projects.
    
    In Odoo 19, projects are created from sale order lines via the
    _timesheet_create_project() method. We extend the prepare_values hook
    to include PTT event-specific fields when creating the project.
    
    PROJECT TEMPLATE SELECTION:
    Each Event Kickoff product is directly linked to its project template:
    - Event Kickoff - Corporate → Corporate Event Project Template
    - Event Kickoff - Wedding → Wedding Event Project Template
    - Event Kickoff - Social → Social Event Project Template
    
    No template-swapping code needed - sales reps simply choose the right
    Event Kickoff product and Odoo uses its linked template automatically.
    """
    _inherit = 'sale.order.line'

    def _timesheet_create_project_prepare_values(self):
        """Extend project creation values with event-specific fields from the sale order.
        
        This is the proper Odoo 19 hook point for including custom fields when
        creating a project from a sale order line.
        
        Project naming convention: "Client Name - Event Name - SO Number"
        Example: "Johnson Family - Smith Wedding Reception - S00042"
        """
        values = super()._timesheet_create_project_prepare_values()
        
        order = self.order_id
        
        # =======================================================================
        # PROJECT NAME: "Client Name - Event Name - SO Number"
        # =======================================================================
        # Use partner name (client) + event name + sale order number for clear identification
        client_name = order.partner_id.name if order.partner_id else 'Unknown Client'
        event_name = order.event_name or ''
        so_number = order.name or 'Draft'
        
        if event_name:
            values['name'] = f"{client_name} - {event_name} - {so_number}"
        else:
            values['name'] = f"{client_name} - {so_number}"
        
        # Link to CRM opportunity - all event fields are related/computed from CRM
        # Setting ptt_crm_lead_id auto-populates: event name, date, times, venue, etc.
        if order.opportunity_id:
            values['ptt_crm_lead_id'] = order.opportunity_id.id
        
        return values
