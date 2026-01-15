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
    
    ptt_event_id = fields.Char(
        string="Event ID",
        related="opportunity_id.ptt_event_id",
        readonly=True,
        store=True,
        help="Unique event identifier linking CRM, Sales Order, and Project",
    )
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
            # Link project to CRM and copy event fields (including Event ID)
            project.write({
                'ptt_crm_lead_id': lead.id,
                'ptt_event_id': lead.ptt_event_id,  # Auto-link Event ID from CRM
                'ptt_event_type': lead.ptt_event_type,
                'ptt_event_date': lead.ptt_event_date,
                'ptt_guest_count': lead.ptt_estimated_guest_count,
                'ptt_venue_name': lead.ptt_venue_name,
            })
            # Backlink CRM to project
            lead.write({'ptt_project_id': project.id})
