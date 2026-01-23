# Part of Party Time Texas Event Management System
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import models, fields, api, _


class CrmLeadEnhanced(models.Model):
    """Enhanced CRM Lead with Event Type Integration.
    
    NOTE: Services are selected as PRODUCT VARIANTS during quotation building,
    NOT as checkboxes on the CRM lead. The checkboxes in ptt_business_core
    are for initial lead capture only - actual service selection happens
    when building the quote with product variants.
    """
    _inherit = 'crm.lead'

    # ==========================================================================
    # EVENT TYPE - Simple Selection Field (REQUIRED)
    # ==========================================================================
    # ptt_event_type is the source of truth for event type classification.
    # Sale Order and Project get this value via related fields.
    # Auto-populates the correct Event Kickoff product on quotations.
    
    ptt_event_type = fields.Selection(
        selection=[
            ('corporate', 'Corporate'),
            ('social', 'Social'),
            ('wedding', 'Wedding'),
        ],
        string="Event Type",
        required=True,
        tracking=True,
        help="Type of event - determines Event Kickoff product on quotations. "
             "Corporate, Social, or Wedding.",
    )

    def action_create_quotation(self):
        """Override to auto-add Event Kickoff product and copy service lines.
        
        NOTE: Event details (name, date, venue, guest count, etc.) are automatically
        synced via RELATED FIELDS on sale.order that link to opportunity_id.
        No manual copying needed - CRM is the single source of truth!
        
        Flow:
        1. Create the quotation (super()) - this sets opportunity_id
        2. Related fields auto-populate event details from CRM
        3. Auto-add the correct Event Kickoff product based on event type
        4. Copy any CRM service lines to the quotation
        """
        quotation_action = super().action_create_quotation()
        
        # Get the created quotation
        if quotation_action.get('res_id'):
            quotation = self.env['sale.order'].browse(quotation_action['res_id'])
            
            # Event details are automatically populated via related fields!
            # The quotation.opportunity_id points to this CRM lead, so all
            # event_name, event_guest_count, event_venue, etc. are synced.
            
            # Auto-add the correct Event Kickoff product based on event type
            if self.ptt_event_type:
                quotation._add_event_kickoff_from_crm()
            
            # Copy any CRM service lines to the quotation
            self._ptt_copy_service_lines_to_order(quotation)
        
        return quotation_action

    def _ptt_copy_service_lines_to_order(self, order):
        """Create sale order lines from CRM service lines when possible."""
        self.ensure_one()
        service_lines = self.ptt_service_line_ids
        if not service_lines:
            return
        if order.order_line:
            order.message_post(
                body=_("Service lines were not copied because the quotation already has lines."),
                message_type="notification",
            )
            return

        order_line_vals = []
        missing_product_lines = self.env["ptt.crm.service.line"]

        for line in service_lines:
            if not line.product_id:
                missing_product_lines |= line
                continue
            qty = line.quantity or 0.0
            if line.hours and line.hours > 0:
                qty = line.hours * (line.quantity or 1.0)
            order_line_vals.append({
                "order_id": order.id,
                "product_id": line.product_id.id,
                "product_uom_qty": qty,
                "price_unit": line.unit_price,
                "name": line.name,
            })

        if order_line_vals:
            self.env["sale.order.line"].create(order_line_vals)

        if missing_product_lines:
            missing_names = ", ".join(missing_product_lines.mapped("name"))
            order.message_post(
                body=_(
                    "Some service lines were not copied because they have no product set: %s",
                    missing_names or _("(unnamed)"),
                ),
                message_type="notification",
            )
