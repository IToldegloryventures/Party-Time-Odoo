# Part of Party Time Texas Event Management System
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models


class SaleOrderLine(models.Model):
    """Extend sale.order.line to include event details when creating projects.
    
    In Odoo 19, projects are created from sale order lines via the
    _timesheet_create_project() method. We extend _timesheet_create_project_prepare_values()
    to include Party Time Texas event-specific fields when a project is created
    from a sale order with event details.
    """
    _inherit = 'sale.order.line'

    def _timesheet_create_project_prepare_values(self):
        """Extend project creation values with event-specific fields from the sale order.
        
        This is the proper Odoo 19 hook point for including custom fields when
        creating a project from a sale order line.
        """
        values = super()._timesheet_create_project_prepare_values()
        
        order = self.order_id
        if order.event_type_id:
            # Add Party Time Texas event fields
            event_vals = {
                'ptt_event_type_id': order.event_type_id.id,
                'ptt_event_name': order.event_name,
                'ptt_guest_count': order.event_guest_count,
                'ptt_venue_name': order.event_venue,
                'ptt_setup_start_time': order.setup_time,
                'ptt_teardown_deadline': order.breakdown_time,
                'ptt_total_hours': order.event_duration,
            }
            
            # Handle event_date (Datetime) -> project date fields
            if order.event_date:
                event_vals['ptt_event_date'] = order.event_date.date() if hasattr(order.event_date, 'date') else order.event_date
                event_vals['ptt_event_start_time'] = order.event_date
                if order.event_duration:
                    event_vals['ptt_event_end_time'] = fields.Datetime.add(order.event_date, hours=order.event_duration)
            
            values.update(event_vals)
        
        return values
