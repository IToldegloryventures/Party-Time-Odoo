import logging

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


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

    @api.depends("amount_total", "opportunity_id.ptt_estimated_guest_count")
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
        """Override create to auto-add Event Kickoff product.
        
        When a quotation is created from a CRM lead,
        automatically adds Event Kickoff product if not already present.
        
        NOTE: Services should be added directly in the quotation (not from CRM service lines)
        to support product variants properly (Event Type + Tier attributes).
        """
        orders = super().create(vals_list)
        
        # Auto-add Event Kickoff for orders with opportunities
        for order in orders:
            if order.opportunity_id:
                # Auto-add Event Kickoff if not already in order
                self._ensure_event_kickoff(order)
        
        return orders
    
    def write(self, vals):
        """Override write to auto-add Event Kickoff when opportunity_id is set.
        
        Handles cases where:
        - Quotation is created without opportunity_id, then opportunity_id is set later
        - Services are added via "Generate Quote" button or other actions
        
        NOTE: Services should be added directly in the quotation (not from CRM service lines)
        to support product variants properly (Event Type + Tier attributes).
        """
        result = super().write(vals)
        
        # If opportunity_id was just set, auto-add Event Kickoff
        if 'opportunity_id' in vals and vals['opportunity_id']:
            for order in self:
                if order.opportunity_id and order.state in ('draft', 'sent'):
                    # Auto-add Event Kickoff if not already in order
                    self._ensure_event_kickoff(order)
        
        return result
    
    def _ensure_event_kickoff(self, order):
        """Ensure Event Kickoff product is added to the order.
        
        Event Kickoff is a $0 product that triggers project creation
        with standard tasks when the sales order is confirmed.
        """
        # Find Event Kickoff product
        kickoff_product = self.env.ref('ptt_business_core.product_event_kickoff', raise_if_not_found=False)
        if not kickoff_product:
            _logger.warning(
                "Event Kickoff product (ptt_business_core.product_event_kickoff) not found for Sale Order %s. "
                "Auto-project creation features will not work. Please ensure the product data is loaded.",
                order.name
            )
            return
        
        # Check if Event Kickoff is already in the order
        existing_product_ids = set(order.order_line.mapped('product_id').ids)
        if kickoff_product.id in existing_product_ids:
            return
        
        # Add Event Kickoff as first line (sequence -99 to ensure it's first)
        self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': kickoff_product.id,
            'product_uom_qty': 1.0,
            'product_uom_id': kickoff_product.uom_id.id,
            'name': kickoff_product.name,
            'price_unit': 0.0,  # $0 price
            'sequence': -99,  # Put it first
        })
    
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
        """Override SO confirmation to update CRM stage.
        
        When SO is confirmed (customer accepts):
        - Move CRM to 'Booked' stage
        
        NOTE: Auto project creation has been DISABLED.
        User will create projects manually and link them as needed.
        
        Reference: https://www.odoo.com/documentation/19.0/developer/reference/backend/orm.html
        """
        res = super().action_confirm()
        
        for order in self:
            if order.state == 'sale':
                order.message_post(
                    body=_("Order confirmed by customer."),
                    message_type="notification",
                )
                
                # Move CRM to Booked stage (if linked to opportunity)
                if order.opportunity_id:
                    self._update_crm_stage(
                        "Booked",
                        _("CRM stage updated to Booked: Customer confirmed order.")
                    )
        
        return res

    # AUTO PROJECT CREATION DISABLED - User will create projects manually
    # The following methods are commented out but kept for reference:
    # - _link_crm_to_project()
    # - _create_service_specific_tasks()
