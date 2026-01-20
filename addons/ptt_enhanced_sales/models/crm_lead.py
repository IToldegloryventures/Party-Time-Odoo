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

    @api.onchange('ptt_event_type_id')
    def _onchange_ptt_event_type_id(self):
        """Sync ptt_event_type selection field when template is changed.
        
        Maps the sale.order.type name to the corresponding selection value
        so both fields stay consistent.
        """
        if self.ptt_event_type_id:
            type_name = self.ptt_event_type_id.name.lower() if self.ptt_event_type_id.name else ''
            if 'corporate' in type_name:
                self.ptt_event_type = 'corporate'
            elif 'wedding' in type_name:
                self.ptt_event_type = 'wedding'
            elif 'social' in type_name:
                self.ptt_event_type = 'social'

    @api.onchange('ptt_event_type')
    def _onchange_ptt_event_type(self):
        """Sync ptt_event_type_id template when selection field is changed.
        
        Auto-links to the matching sale.order.type template based on selection.
        This ensures the template is set when users pick from the simple dropdown.
        """
        if self.ptt_event_type and not self.ptt_event_type_id:
            # Map selection to XML ID
            xmlid_map = {
                'corporate': 'ptt_enhanced_sales.event_type_corporate',
                'social': 'ptt_enhanced_sales.event_type_social',
                'wedding': 'ptt_enhanced_sales.event_type_wedding',
            }
            xmlid = xmlid_map.get(self.ptt_event_type)
            if xmlid:
                event_type = self.env.ref(xmlid, raise_if_not_found=False)
                if event_type:
                    self.ptt_event_type_id = event_type

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
                'event_name': self.ptt_event_name or self.name,
                'event_guest_count': self.ptt_guest_count or 0,
                'event_venue': self.ptt_venue_name or '',
            }
            
            # Only set event_date if we have one (Date→Datetime conversion)
            if self.ptt_event_date:
                quotation_vals['event_date'] = fields.Datetime.to_datetime(self.ptt_event_date)
            
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
