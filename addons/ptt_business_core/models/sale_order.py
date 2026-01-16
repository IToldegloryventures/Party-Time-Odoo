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
        5. Creates service-specific tasks for each product/service in the order
        
        Reference: https://www.odoo.com/documentation/19.0/developer/reference/backend/orm.html
        """
        if not order.opportunity_id:
            return
        
        lead = order.opportunity_id
        
        # Find project that Odoo created via service_tracking
        # Odoo links projects via sale_order_id (related from sale_line_id) or reinvoiced_sale_order_id
        # Reference: odoo/addons/sale_project/models/project_project.py
        project = self.env['project.project'].search([
            '|',
            ('sale_order_id', '=', order.id),
            ('reinvoiced_sale_order_id', '=', order.id),
        ], limit=1)
        
        if project:
            # CRITICAL: Ensure project has type_ids (task stages) to prevent frontend OwlError
            # If project was created from template but lacks stages, assign them
            if not project.type_ids:
                task_stages = self.env['project.task.type'].search([])
                if task_stages:
                    project.type_ids = [(6, 0, task_stages.ids)]
                else:
                    # Create default stages if none exist
                    default_stages = self.env['project.task.type'].create([
                        {'name': 'To Do', 'sequence': 5},
                        {'name': 'In Progress', 'sequence': 10},
                        {'name': 'Done', 'sequence': 15},
                        {'name': 'Cancelled', 'sequence': 20, 'fold': True},
                    ])
                    project.type_ids = [(6, 0, default_stages.ids)]
            
            # Link project to CRM and copy event fields
            # Use safe field access - only set fields that exist
            # Reference: Odoo 19 official docs - safe field population pattern
            project_vals = {
                'ptt_crm_lead_id': lead.id,
            }
            
            # Safely copy CRM event fields to project (using safe attribute access)
            if hasattr(lead, 'ptt_event_type') and lead.ptt_event_type:
                project_vals['ptt_event_type'] = lead.ptt_event_type
            if hasattr(lead, 'ptt_event_date') and lead.ptt_event_date:
                project_vals['ptt_event_date'] = lead.ptt_event_date
            if hasattr(lead, 'ptt_estimated_guest_count') and lead.ptt_estimated_guest_count:
                project_vals['ptt_guest_count'] = lead.ptt_estimated_guest_count
            if hasattr(lead, 'ptt_venue_name') and lead.ptt_venue_name:
                project_vals['ptt_venue_name'] = lead.ptt_venue_name
            if hasattr(lead, 'ptt_event_time') and lead.ptt_event_time:
                project_vals['ptt_event_time'] = lead.ptt_event_time
            
            # Also set standard project fields from sales order and CRM
            # CRITICAL: company_id must be set for Odoo 19 to prevent frontend OwlError
            # Odoo 19 requires company_id for multi-company safety
            if not project.company_id:
                project_vals['company_id'] = order.company_id.id if order.company_id else self.env.company.id
            
            # CRITICAL: partner_id must be set to prevent OwlError
            # Use sale order partner first, then CRM lead partner, then fallback to any existing partner
            if order.partner_id:
                project_vals['partner_id'] = order.partner_id.id
            elif lead.partner_id:
                project_vals['partner_id'] = lead.partner_id.id
            elif not project.partner_id:
                # Use any existing partner as fallback (safer than setting False or XML ID reference)
                fallback_partner = self.env['res.partner'].search([], limit=1)
                if fallback_partner:
                    project_vals['partner_id'] = fallback_partner.id
            
            # Set project assignee from CRM Lead Salesperson (user_id)
            # This should auto-populate from contact card if salesperson exists there
            # Reference: CRM Lead user_id = Salesperson field
            if lead.user_id:
                project_vals['user_id'] = lead.user_id.id
            # Note: user_id is optional, so we don't set a fallback if it doesn't exist
                
            if order.ptt_event_date:
                project_vals['date_start'] = order.ptt_event_date  # Standard project field
            
            project.write(project_vals)
            # Backlink CRM to project
            lead.write({'ptt_project_id': project.id})
            
            # Create service-specific tasks for each product in the order (except Event Kickoff)
            self._create_service_specific_tasks(order, project)
    
    def _create_service_specific_tasks(self, order, project):
        """Create service-specific tasks for each product/service in the sales order.
        
        After project is created via Event Kickoff, create tasks for each service/product
        to track work for that specific service type.
        
        Tasks are assigned to the CRM Lead Salesperson (user_id) if one is assigned.
        This should auto-populate from contact card if salesperson exists there.
        
        Args:
            order: The confirmed sales order
            project: The project that was just created
        """
        # Find Event Kickoff product to exclude it
        kickoff_product = self.env.ref('ptt_business_core.product_event_kickoff', raise_if_not_found=False)
        kickoff_product_id = kickoff_product.id if kickoff_product else None
        
        # Get all order lines with products (excluding Event Kickoff)
        service_lines = order.order_line.filtered(
            lambda l: l.product_id and l.product_id.id != kickoff_product_id
        )
        
        if not service_lines:
            return
        
        # CRITICAL: Get first stage_id for tasks to prevent frontend OwlError
        # Tasks MUST have stage_id set or the frontend crashes
        # Reference: Odoo 19 official docs - project.task must have stage_id
        first_stage = False
        if project.type_ids and len(project.type_ids) > 0:
            first_stage = project.type_ids[0]
        if not first_stage:
            # Fallback: get any available stage or create default
            first_stage = self.env['project.task.type'].search([], limit=1)
            if not first_stage:
                first_stage = self.env['project.task.type'].create({
                    'name': 'To Do',
                    'sequence': 5,
                })
        
        # Build event context for task descriptions (using safe getattr for CRM fields)
        # Reference: Odoo 19 official docs - safe field access pattern
        event_context_parts = []
        if order.ptt_event_date:
            event_context_parts.append(f"Event Date: {order.ptt_event_date}")
        if order.ptt_event_time:
            event_context_parts.append(f"Event Time: {order.ptt_event_time}")
        if order.ptt_venue_name:
            event_context_parts.append(f"Venue: {order.ptt_venue_name}")
        if order.ptt_guest_count:
            event_context_parts.append(f"Guest Count: {order.ptt_guest_count}")
        if order.ptt_event_type:
            # Get readable label from selection field
            event_type_label = dict(order._fields['ptt_event_type'].selection).get(
                order.ptt_event_type, order.ptt_event_type
            ) if hasattr(order, '_fields') and 'ptt_event_type' in order._fields else order.ptt_event_type
            if event_type_label:
                event_context_parts.append(f"Event Type: {event_type_label}")
        
        event_context = "\n".join(event_context_parts) if event_context_parts else ""
        
        # Create a task for each service/product
        task_vals_list = []
        sequence = 100  # Start after standard template tasks (which are sequence 10-90)
        
        for line in service_lines:
            # Format task name as "[SERVICE] TASK"
            # Use product name, convert to uppercase, append " TASK"
            service_name = line.product_id.name.upper() if line.product_id.name else "SERVICE"
            task_name = f"{service_name} TASK"
            
            # Build rich task description with service and event context
            description_parts = [
                f"Service: {line.name}",
                f"Quantity: {line.product_uom_qty} {line.product_uom_id.name if line.product_uom_id else 'units'}",
                f"Unit Price: ${line.price_unit:.2f}",
            ]
            if event_context:
                description_parts.append("")  # Empty line separator
                description_parts.append("Event Details:")
                description_parts.append(event_context)
            
            task_vals = {
                'name': task_name,
                'project_id': project.id,
                'sale_line_id': line.id,
                'sale_order_id': order.id,
                'partner_id': order.partner_id.id if order.partner_id else False,
                'stage_id': first_stage.id,  # CRITICAL: Must set stage_id to prevent OwlError
                'description': "\n".join(description_parts),
                'sequence': sequence,
            }
            
            # Assign to CRM Lead Salesperson (user_id) if one is assigned
            # This should auto-populate from contact card if salesperson exists there
            # Reference: CRM Lead user_id = Salesperson field
            if order.opportunity_id and order.opportunity_id.user_id:
                task_vals['user_ids'] = [(4, order.opportunity_id.user_id.id)]  # Assign to CRM Salesperson (Many2many command)
            
            task_vals_list.append(task_vals)
            sequence += 10
        
        # Create all tasks at once
        if task_vals_list:
            self.env['project.task'].create(task_vals_list)
