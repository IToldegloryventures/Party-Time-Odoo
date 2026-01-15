from odoo import models, fields, api, _


class SaleOrder(models.Model):
    """Extend Sale Order with PTT CRM stage automation and event details.
    
    CRM Stage Workflow:
    1. Quote/Proposal Sent → CRM moves to "Proposal Sent"
    2. Customer Accepts (SO Confirmed) → CRM moves to "Booked"
    
    Event Details:
    - Related fields pull Tier 1 info from CRM for display on quote
    - Price Per Person computed from quote total ÷ guest count
    
    NOTE: Contract status = Use standard 'state' field (draft/sent/sale)
    NOTE: Contract signed date = Use standard 'date_order' when state='sale'
    
    Reference:
    - https://www.odoo.com/documentation/19.0/applications/sales/sales.html
    - https://www.odoo.com/documentation/19.0/developer/reference/backend/orm.html#related-fields
    """
    _inherit = "sale.order"

    # === EVENT DETAILS (Related from CRM Lead) ===
    # These fields pull Tier 1 info from the linked CRM opportunity
    # for display on quotations and sales orders.
    # Reference: https://www.odoo.com/documentation/19.0/developer/reference/backend/orm.html#related-fields
    
    ptt_event_date = fields.Date(
        string="Event Date",
        related="opportunity_id.ptt_event_date",
        readonly=True,
        store=True,
    )
    ptt_event_type = fields.Selection(
        related="opportunity_id.ptt_event_type",
        readonly=True,
        store=True,
        string="Event Type",
    )
    ptt_venue_name = fields.Char(
        string="Venue",
        related="opportunity_id.ptt_venue_name",
        readonly=True,
        store=True,
    )
    ptt_guest_count = fields.Integer(
        string="Guest Count",
        related="opportunity_id.ptt_estimated_guest_count",
        readonly=True,
        store=True,
        help="Estimated guest count from CRM lead",
    )
    ptt_event_time = fields.Char(
        string="Event Time",
        related="opportunity_id.ptt_event_time",
        readonly=True,
        store=True,
    )

    # === PRICE PER PERSON (Computed) ===
    # Shows value proposition to client: total cost divided by guests
    # Reference: https://www.odoo.com/documentation/19.0/developer/reference/backend/orm.html#compute-methods
    ptt_price_per_person = fields.Monetary(
        string="Price Per Person",
        compute="_compute_price_per_person",
        store=True,
        currency_field="currency_id",
        help="Quote total divided by guest count. Shows value proposition to client.",
    )

    @api.depends("amount_total", "ptt_guest_count")
    def _compute_price_per_person(self):
        """Calculate price per person from quote total and guest count.
        
        Formula: amount_total ÷ ptt_guest_count
        
        If guest count is 0 or missing, price per person = 0
        """
        for order in self:
            if order.ptt_guest_count and order.ptt_guest_count > 0:
                order.ptt_price_per_person = order.amount_total / order.ptt_guest_count
            else:
                order.ptt_price_per_person = 0.0

    # === CREATE ORDER LINES FROM SERVICE LINES ===
    
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to auto-populate order lines from service lines.
        
        When a quotation is created from a CRM lead with service lines,
        automatically create sale order lines from those service lines.
        """
        orders = super().create(vals_list)
        
        # Create order lines from service lines for orders with opportunities
        for order in orders:
            if order.opportunity_id and order.opportunity_id.ptt_service_line_ids:
                self._create_order_lines_from_service_lines(order)
        
        return orders
    
    def _create_order_lines_from_service_lines(self, order):
        """Create sale order lines from CRM service lines.
        
        Maps service line fields to sale order line fields:
        - product_id → product_id
        - estimated_price → price_unit
        - description → name (or product name if no description)
        - tier/service_type → stored in description or notes
        """
        if not order.opportunity_id or not order.opportunity_id.ptt_service_line_ids:
            return
        
        # Only create lines if order doesn't already have lines
        # This prevents duplicating lines when editing an existing quotation
        if order.order_line:
            return
        
        service_lines = order.opportunity_id.ptt_service_line_ids.sorted('sequence')
        order_line_vals = []
        
        for service_line in service_lines:
            # Skip if no product selected
            if not service_line.product_id:
                continue
            
            # Build description from service line
            name_parts = []
            if service_line.product_id.name:
                name_parts.append(service_line.product_id.name)
            if service_line.tier and service_line.tier != 'classic':
                tier_label = dict(service_line._fields['tier'].selection).get(
                    service_line.tier, service_line.tier
                )
                name_parts.append(f"({tier_label})")
            if service_line.description:
                name_parts.append(f"- {service_line.description}")
            
            name = " ".join(name_parts) if name_parts else service_line.product_id.name
            
            # Prepare order line values
            line_vals = {
                'order_id': order.id,
                'product_id': service_line.product_id.id,
                'product_uom_qty': 1.0,  # Default quantity
                'product_uom_id': service_line.product_id.uom_id.id,
                'name': name,
                'sequence': service_line.sequence if service_line.sequence else 10,
            }
            
            # Set price if provided in service line
            if service_line.estimated_price:
                line_vals['price_unit'] = service_line.estimated_price
            # Otherwise, price will be computed by Odoo's onchange when product is set
            
            order_line_vals.append(line_vals)
        
        # Create order lines directly if any were prepared
        if order_line_vals:
            # Create order lines using create_multi for better performance
            self.env['sale.order.line'].create(order_line_vals)

    # === CRM STAGE AUTOMATION ===
    
    def _update_crm_stage(self, stage_name, message=None):
        """Helper to update CRM stage for linked opportunity.
        
        Args:
            stage_name: Name of the CRM stage to move to
            message: Optional message to post on the CRM lead
        """
        for order in self:
            if order.opportunity_id:
                stage = self.env["crm.stage"].search(
                    [("name", "=", stage_name)], limit=1
                )
                if stage and order.opportunity_id.stage_id != stage:
                    order.opportunity_id.stage_id = stage.id
                    if message:
                        order.opportunity_id.message_post(
                            body=message,
                            message_type="notification",
                        )

    def action_quotation_sent(self):
        """Override: When quote/proposal is sent, update CRM to 'Proposal Sent'.
        
        This is triggered when user clicks "Send by Email" on the quotation.
        """
        res = super().action_quotation_sent()
        self._update_crm_stage(
            "Proposal Sent",
            _("CRM stage updated: Quote sent to customer for review.")
        )
        return res

    def action_confirm(self):
        """Override SO confirmation to update CRM stage and link project.
        
        When SO is confirmed (customer accepts):
        - Move CRM to 'Booked' stage
        - Link CRM lead to project (bidirectional)
        - Copy CRM event fields to project
        
        IMPORTANT: Odoo creates the project via service_tracking on Event Kickoff product.
        We do NOT create it manually - we just link CRM after Odoo creates it.
        
        Reference: https://www.odoo.com/documentation/19.0/developer/reference/backend/orm.html
        """
        res = super().action_confirm()  # Odoo creates project here via service_tracking
        
        for order in self:
            if order.state == 'sale':
                order.message_post(
                    body=_("Order confirmed by customer."),
                    message_type="notification",
                )
                
                # Move CRM to Booked stage and link to project (if linked to opportunity)
                if order.opportunity_id:
                    self._update_crm_stage(
                        "Booked",
                        _("CRM stage updated to Booked: Customer confirmed order.")
                    )
                    # Link CRM to project that Odoo created
                    self._link_crm_to_project(order)
        
        return res

    def _link_crm_to_project(self, order):
        """Link CRM lead to project that Odoo created via service_tracking.
        
        This method:
        1. Finds the project Odoo created (via sale_order_id)
        2. Links project to CRM lead (ptt_crm_lead_id)
        3. Copies CRM event fields to project
        4. Backlinks CRM to project (ptt_project_id)
        
        Reference: https://www.odoo.com/documentation/19.0/developer/reference/backend/orm.html
        """
        if not order.opportunity_id:
            return
        
        lead = order.opportunity_id
        
        # Find project that Odoo created via service_tracking
        project = self.env['project.project'].search([
            ('sale_order_id', '=', order.id),
        ], limit=1)
        
        if project:
            # Link project to CRM and copy event fields
            project.write({
                'ptt_crm_lead_id': lead.id,
                'ptt_event_type': lead.ptt_event_type,
                'ptt_event_date': lead.ptt_event_date,
                'ptt_guest_count': lead.ptt_estimated_guest_count,
                'ptt_venue_name': lead.ptt_venue_name,
            })
            # Backlink CRM to project
            lead.write({'ptt_project_id': project.id})
