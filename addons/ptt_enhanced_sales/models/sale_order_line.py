# Part of Party Time Texas Event Management System
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models
import logging

_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    """Extend sale.order.line to include event details when creating projects.
    
    In Odoo 19, projects are created from sale order lines via the
    _timesheet_create_project() method. We extend this to:
    
    1. Use the event type's native project template (instead of product's default)
    2. Include PTT event-specific fields when creating the project
    
    The 9 standard event tasks come from the PROJECT TEMPLATE (XML data),
    not from programmatic creation. This allows customization per event type.
    """
    _inherit = 'sale.order.line'

    def _timesheet_create_project_prepare_values(self):
        """Extend project creation values with event-specific fields from the sale order.
        
        This is the proper Odoo 19 hook point for including custom fields when
        creating a project from a sale order line.
        """
        values = super()._timesheet_create_project_prepare_values()
        
        order = self.order_id
        if order.event_type_id or order.event_name:
            # Add Party Time Texas event fields (use Studio fields directly)
            event_vals = {
                'ptt_event_name': order.event_name,
                'ptt_guest_count': order.event_guest_count,
                'ptt_venue_name': order.event_venue,
                'ptt_setup_start_time': order.setup_time,
                'ptt_teardown_deadline': order.breakdown_time,
                'ptt_total_hours': order.event_duration,
            }
            
            if order.event_type_id:
                event_vals['ptt_event_type_id'] = order.event_type_id.id
            
            # Handle event_date (Datetime) -> project date fields
            if order.event_date:
                event_vals['ptt_event_date'] = order.event_date.date() if hasattr(order.event_date, 'date') else order.event_date
                event_vals['ptt_event_start_time'] = order.event_date
                if order.event_duration:
                    event_vals['ptt_event_end_time'] = fields.Datetime.add(order.event_date, hours=order.event_duration)
            
            # Link to CRM opportunity if available
            if order.opportunity_id:
                event_vals['ptt_crm_lead_id'] = order.opportunity_id.id
            
            values.update(event_vals)
        
        return values

    def _timesheet_create_project(self):
        """Override to use the event type's native project template.
        
        When the Event Kickoff product creates a project:
        1. Check if the Sale Order has an event type with a linked native template
        2. If so, temporarily swap the product's template with the event type's template
        3. Let Odoo's native template copying create the project with all tasks
        
        This ensures the correct template (Corporate/Wedding/Social) is used
        based on the Sale Order's event type, while using Odoo's native
        template copying mechanism for tasks and subtasks.
        """
        # Check if this is an Event Kickoff product
        is_event_kickoff = self.product_id.default_code == 'EVENT-KICKOFF'
        original_template = None
        event_type_template = None
        
        if is_event_kickoff:
            order = self.order_id
            # Get the event type's native project template
            if order.event_type_id and hasattr(order.event_type_id, 'native_project_template_id'):
                event_type_template = order.event_type_id.native_project_template_id
                
                if event_type_template:
                    # Store the product's original template
                    original_template = self.product_id.project_template_id
                    
                    # Temporarily set the product's template to the event type's template
                    # This makes Odoo's native _timesheet_create_project use the correct template
                    _logger.info(
                        "Event Kickoff: Using template '%s' for event type '%s'",
                        event_type_template.name,
                        order.event_type_id.name
                    )
                    self.product_id.write({'project_template_id': event_type_template.id})
        
        try:
            # Call parent to create the project using the (possibly swapped) template
            # Odoo's native code will copy all tasks from the template
            project = super()._timesheet_create_project()
        finally:
            # Restore the original template on the product
            if is_event_kickoff and original_template is not None:
                self.product_id.write({'project_template_id': original_template.id})
        
        return project