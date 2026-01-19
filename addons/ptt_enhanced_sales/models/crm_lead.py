# Part of Party Time Texas Event Management System
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import models, fields, api, _


class CrmLeadEnhanced(models.Model):
    """Enhanced CRM Lead with Event Type Integration.
    
    This extends the ptt_business_core CRM Lead with event type
    classification from sale.order.type.
    
    NOTE: Services are selected as PRODUCT VARIANTS during quotation building,
    NOT as checkboxes on the CRM lead. The checkboxes in ptt_business_core
    are for initial lead capture only - actual service selection happens
    when building the quote with product variants.
    """
    _inherit = 'crm.lead'

    # Event Type Integration - links to sale.order.type
    ptt_event_type_id = fields.Many2one(
        'sale.order.type',
        string="Event Type Template",
        help="Predefined event type template (Corporate/Social/Wedding) - used to set defaults on quotation"
    )
    
    # NOTE: Category field removed - event type name (Corporate/Social/Wedding) is the category
    
    def action_create_quotation(self):
        """Override to include event type information in quotation.
        
        Services are NOT copied from CRM checkboxes - they are selected
        as product variants during quotation building.
        """
        quotation_action = super().action_create_quotation()
        
        # Get the created quotation
        if quotation_action.get('res_id'):
            quotation = self.env['sale.order'].browse(quotation_action['res_id'])
            
            # Populate event type and basic details from lead
            # Services will be added as product variants, not from checkboxes
            quotation_vals = {
                'event_type_id': self.ptt_event_type_id.id if self.ptt_event_type_id else False,
                'event_name': self.x_studio_event_name or self.name,
                'event_guest_count': self.ptt_guest_count or 0,
                'event_venue': self.x_studio_venue_name or '',
            }
            
            # Only set event_date if we have one (Date→Datetime conversion)
            if self.x_studio_event_date:
                quotation_vals['event_date'] = fields.Datetime.to_datetime(self.x_studio_event_date)
            
            quotation.write(quotation_vals)
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
