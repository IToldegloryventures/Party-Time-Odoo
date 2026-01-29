# Part of Party Time Texas Event Management System
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import models, fields, api


class SaleOrderType(models.Model):
    """Event Type Classification for Sales Orders"""
    _name = 'sale.order.type'
    _description = 'Sale Order Type - Event Classification'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, name'

    name = fields.Char(
        string="Event Type Name",
        required=True,
        help="Name of the event type (e.g., Corporate Conference, Wedding)"
    )
    
    code = fields.Char(
        string="Code",
        help="Short code for the event type (e.g., CORP_CONF, WEDDING)"
    )
    
    sequence = fields.Integer(
        string="Sequence",
        default=10,
        help="Order of event types in selection lists"
    )
    
    active = fields.Boolean(
        string="Active",
        default=True,
        help="Uncheck to hide this event type"
    )
    
    description = fields.Text(
        string="Description",
        help="Detailed description of this event type"
    )
    
    # NOTE: Category field removed - the event type name (Corporate/Social/Wedding)
    # itself serves as the category. This simplifies the model to match
    # the 3 event types defined in product_attributes.xml
    
    # Workflow Settings
    requires_approval = fields.Boolean(
        string="Requires Approval",
        default=False,
        help="Orders of this type require management approval"
    )
    
    approval_amount = fields.Float(
        string="Approval Amount Threshold",
        help="Orders above this amount require approval"
    )
    
    # Default Duration and Timing
    default_duration_hours = fields.Float(
        string="Default Duration (Hours)",
        help="Typical duration for this event type"
    )
    
    default_setup_hours = fields.Float(
        string="Default Setup Time (Hours)",
        help="Typical setup time needed"
    )
    
    default_breakdown_hours = fields.Float(
        string="Default Breakdown Time (Hours)",
        help="Typical breakdown time needed"
    )

    quotation_template_id = fields.Many2one(
        "sale.order.template",
        string="Default Quotation Template",
        help="Quotation template automatically applied when this event type is selected.",
    )

    # Color for visual identification
    color = fields.Integer(
        string="Color Index",
        help="Color for displaying this event type in views"
    )
    
    @api.model
    def get_all_event_types(self):
        """Get all active event types for selection.
        
        Returns:
            List of dicts with event type info (id, name, code)
        """
        return self.search([('active', '=', True)]).read(['name', 'code'])
