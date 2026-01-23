# Part of Party Time Texas Event Management System
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import models, fields, api, _

from odoo.addons.ptt_business_core.constants import LOCATION_TYPES, TIME_SELECTIONS

# Map event type Selection values to Event Kickoff product internal references
# These products are defined in ptt_business_core/data/products_administrative.xml
EVENT_KICKOFF_PRODUCTS = {
    'corporate': 'EVENT-KICKOFF-CORP',  # Corporate → Event Kickoff - Corporate
    'wedding': 'EVENT-KICKOFF-WEDD',    # Wedding → Event Kickoff - Wedding
    'social': 'EVENT-KICKOFF-SOCL',     # Social → Event Kickoff - Social
}

# All Event Kickoff product codes (for detection/replacement)
ALL_EVENT_KICKOFF_CODES = list(EVENT_KICKOFF_PRODUCTS.values())


class SaleOrder(models.Model):
    """Enhanced Sale Order for Event Management"""
    _inherit = 'sale.order'

    # ==========================================================================
    # EVENT DETAILS - Related fields from CRM Lead (single source of truth)
    # ==========================================================================
    # All event fields are RELATED to opportunity_id (CRM Lead).
    # EDITABLE in Draft/Sent states - changes sync back to CRM.
    # READ-ONLY once order is Confirmed (sale/done) - locked for event execution.
    # View applies readonly="state in ('sale', 'done')" condition.
    
    # Event Type Classification - related to CRM (auto-populates from CRM Lead)
    event_type = fields.Selection(
        related='opportunity_id.ptt_event_type',
        string="Event Type",
        store=True,
        readonly=False,
        help="Type of event (Corporate/Social/Wedding) - auto-populates from CRM Lead"
    )
    
    # Core Event Details - related to CRM
    event_name = fields.Char(
        related='opportunity_id.ptt_event_name',
        string="Event Name",
        store=True,
        readonly=False,
        help="Name of the event"
    )
    
    event_duration = fields.Float(
        related='opportunity_id.ptt_event_duration',
        string="Event Duration (Hours)",
        store=True,
        readonly=False,
        help="Duration in hours"
    )
    
    event_guest_count = fields.Integer(
        related='opportunity_id.ptt_guest_count',
        string="Guest Count",
        store=True,
        readonly=False,
        help="Number of guests"
    )
    
    # Venue Details - related to CRM
    event_venue = fields.Char(
        related='opportunity_id.ptt_venue_name',
        string="Venue Name",
        store=True,
        readonly=False,
        help="Venue name"
    )
    
    event_venue_type = fields.Selection(
        related='opportunity_id.ptt_location_type',
        string="Venue Type",
        store=True,
        readonly=False,
    )
    
    event_venue_address = fields.Text(
        related='opportunity_id.ptt_venue_address',
        string="Address",
        store=True,
        readonly=False,
        help="Venue address"
    )
    
    event_venue_booked = fields.Boolean(
        related='opportunity_id.ptt_venue_booked',
        string="Venue Booked?",
        store=True,
        readonly=False,
    )
    
    event_attire = fields.Selection(
        related='opportunity_id.ptt_attire',
        string="Attire",
        store=True,
        readonly=False,
        help="Dress code"
    )
    
    # Event Date (Date only from CRM)
    event_date_only = fields.Date(
        related='opportunity_id.ptt_event_date',
        string="Event Date",
        store=True,
        readonly=False,
    )
    
    # ==========================================================================
    # EVENT TIMES - Float fields related to CRM
    # ==========================================================================
    # CRM stores times as Float hours. Editable until order confirmed.
    # The Datetime fields below are COMPUTED from Date + Float for display.
    
    event_start_time = fields.Selection(
        selection=TIME_SELECTIONS,
        related='opportunity_id.ptt_start_time',
        string="Start Time",
        store=True,
        readonly=False,
        help="Event start time"
    )
    
    event_end_time = fields.Selection(
        selection=TIME_SELECTIONS,
        related='opportunity_id.ptt_end_time',
        string="End Time", 
        store=True,
        readonly=False,
        help="Event end time"
    )
    
    setup_time_float = fields.Selection(
        selection=TIME_SELECTIONS,
        related='opportunity_id.ptt_setup_time',
        string="Setup Time",
        store=True,
        readonly=False,
        help="Setup start time"
    )
    
    teardown_time_float = fields.Selection(
        selection=TIME_SELECTIONS,
        related='opportunity_id.ptt_teardown_time',
        string="Teardown Time",
        store=True,
        readonly=False,
        help="Teardown/breakdown time"
    )
    
    # Computed Datetime fields - combine Date + Float for display
    # Editable until order confirmed - changes sync back to CRM via inverse methods
    event_date = fields.Datetime(
        string="Event Start",
        compute='_compute_event_datetimes',
        inverse='_inverse_event_date',
        store=True,
        help="Event start date/time"
    )
    
    event_end_datetime = fields.Datetime(
        string="Event End",
        compute='_compute_event_datetimes',
        inverse='_inverse_event_end_datetime',
        store=True,
        help="Event end date/time"
    )
    
    setup_time = fields.Datetime(
        string="Setup Start",
        compute='_compute_event_datetimes',
        inverse='_inverse_setup_time',
        store=True,
        help="Setup start date/time"
    )
    
    breakdown_time = fields.Datetime(
        string="Breakdown/Strike Time",
        help="When breakdown should be completed"
    )
    
    @api.depends('event_date_only', 'event_start_time', 'event_end_time', 'setup_time_float')
    def _compute_event_datetimes(self):
        """Compute Datetime fields from Date + Selection time fields (from CRM).
        
        Selection values are strings like "14.5" representing float hours.
        """
        def selection_to_datetime(date_val, time_selection):
            """Convert Selection string to Datetime."""
            if not time_selection:
                return False
            float_time = float(time_selection)
            hours = int(float_time)
            minutes = int((float_time - hours) * 60)
            return fields.Datetime.to_datetime(date_val).replace(
                hour=hours, minute=minutes, second=0
            )
        
        for order in self:
            if order.event_date_only:
                event_date = order.event_date_only
                
                # Event Start: Date + Start Time
                if order.event_start_time:
                    order.event_date = selection_to_datetime(event_date, order.event_start_time)
                else:
                    order.event_date = fields.Datetime.to_datetime(event_date)
                
                # Event End: Date + End Time
                order.event_end_datetime = selection_to_datetime(event_date, order.event_end_time)
                
                # Setup: Date + Setup Time
                order.setup_time = selection_to_datetime(event_date, order.setup_time_float)
            else:
                order.event_date = False
                order.event_end_datetime = False
                order.setup_time = False
    
    def _datetime_to_selection(self, dt):
        """Convert Datetime to Selection string value (e.g., "14.5").
        
        Rounds to nearest 30 minutes to match TIME_SELECTIONS options.
        """
        if not dt:
            return False
        # Round minutes to 0 or 30
        minutes = 0 if dt.minute < 15 else (30 if dt.minute < 45 else 0)
        hour = dt.hour if dt.minute < 45 else dt.hour + 1
        if hour >= 24:
            hour = 23
            minutes = 30
        return str(hour + minutes / 60.0)
    
    def _inverse_event_date(self):
        """When event_date Datetime is changed, update the CRM Date and Selection time."""
        for order in self:
            if order.event_date and order.opportunity_id:
                order.opportunity_id.ptt_event_date = order.event_date.date()
                order.opportunity_id.ptt_start_time = self._datetime_to_selection(order.event_date)
    
    def _inverse_event_end_datetime(self):
        """When event_end_datetime is changed, update the CRM Selection time."""
        for order in self:
            if order.event_end_datetime and order.opportunity_id:
                order.opportunity_id.ptt_end_time = self._datetime_to_selection(order.event_end_datetime)
    
    def _inverse_setup_time(self):
        """When setup_time Datetime is changed, update the CRM Selection time."""
        for order in self:
            if order.setup_time and order.opportunity_id:
                order.opportunity_id.ptt_setup_time = self._datetime_to_selection(order.setup_time)
    
    # =========================================================================
    # EVENT DETAILS SUMMARY (For Customer-Facing Documents)
    # =========================================================================
    event_details_summary = fields.Text(
        string="Event Details Summary",
        compute="_compute_event_details_summary",
        store=False,
        help="Formatted summary of event details for quotes and contracts"
    )
    
    @api.depends('event_name', 'event_type', 'event_date', 'event_end_datetime',
                 'event_guest_count', 'event_venue', 'event_venue_address', 
                 'event_attire', 'setup_time', 'event_duration')
    def _compute_event_details_summary(self):
        """Generate a formatted summary of event details for customer documents."""
        for order in self:
            lines = []
            
            if order.event_name:
                lines.append(f"Event: {order.event_name}")
            if order.event_type:
                # Get display label from selection
                type_label = dict(order._fields['event_type'].selection).get(order.event_type, order.event_type)
                lines.append(f"Type: {type_label.title()}")
            if order.event_date:
                # Format: "February 6, 2026 at 5:00 PM"
                lines.append(f"Event Start: {order.event_date.strftime('%B %d, %Y at %I:%M %p')}")
            if order.event_end_datetime:
                lines.append(f"Event End: {order.event_end_datetime.strftime('%I:%M %p')}")
            if order.event_duration:
                lines.append(f"Duration: {order.event_duration} hours")
            if order.setup_time:
                lines.append(f"Setup Starts: {order.setup_time.strftime('%I:%M %p')}")
            if order.event_guest_count:
                lines.append(f"Guest Count: {order.event_guest_count}")
            if order.event_attire:
                attire_display = dict(order._fields['event_attire'].selection).get(order.event_attire, '')
                lines.append(f"Attire: {attire_display}")
            if order.event_venue:
                lines.append(f"Venue: {order.event_venue}")
            if order.event_venue_address:
                lines.append(f"Address: {order.event_venue_address}")
            
            order.event_details_summary = '\n'.join(lines) if lines else ''

    # =========================================================================
    # CRM SERVICE LINES (Read-Only Reference)
    # =========================================================================
    ptt_service_line_ids = fields.One2many(
        related="opportunity_id.ptt_service_line_ids",
        string="Service Lines",
        readonly=True,
        help="Service lines captured on the opportunity.",
    )
    ptt_service_lines_total = fields.Monetary(
        related="opportunity_id.ptt_service_lines_total",
        string="Service Lines Total",
        currency_field="currency_id",
        readonly=True,
    )
    
    # =========================================================================
    # CRM STAGE AUTOMATION
    # =========================================================================
    # Odoo 19 Reference: https://www.odoo.com/documentation/19.0/developer/reference/backend/orm.html
    
    def action_quotation_sent(self):
        """Override to update CRM stage when quote is sent.
        
        When a quotation is sent to the customer, automatically:
        1. Call super() to perform standard Odoo quotation send
        2. Update the linked CRM lead to 'Proposal' stage
        3. Mark ptt_proposal_sent flag on the lead
        
        Odoo 19 Reference:
        https://www.odoo.com/documentation/19.0/developer/reference/backend/orm.html#inheritance
        """
        result = super().action_quotation_sent()
        self._update_crm_stage_on_quote_sent()
        return result
    
    def action_confirm(self):
        """Override to update CRM stage when quote is confirmed.
        
        When a quotation is confirmed (becomes a sale order):
        1. Call super() to perform standard Odoo order confirmation
        2. Update the linked CRM lead to 'Won' stage
        3. Set probability to 100% on the lead
        
        Odoo 19 Reference:
        https://www.odoo.com/documentation/19.0/developer/reference/backend/orm.html#inheritance
        """
        result = super().action_confirm()
        self._update_crm_stage_on_order_confirmed()
        return result
    
    def _get_ptt_stage(self, xmlid, fallback_names=None, team=None):
        """Fetch a PTT CRM stage by XML ID, with optional name fallbacks."""
        stage = self.env.ref(xmlid, raise_if_not_found=False)
        if stage:
            return stage
        if not fallback_names:
            return stage
        for name in fallback_names:
            domain = [('name', 'ilike', name)]
            if team:
                domain += ['|', ('team_id', '=', False), ('team_id', '=', team.id)]
            stage = self.env['crm.stage'].search(domain, limit=1)
            if stage:
                return stage
        return stage

    def _update_crm_stage_on_quote_sent(self):
        """Update linked CRM lead stage when quotation is sent.
        
        Finds or creates a 'Proposal' stage and moves the lead to it.
        Also marks the ptt_proposal_sent flag for tracking.
        """
        for order in self:
            lead = order.opportunity_id
            if not lead:
                continue
            
            proposal_stage = self._get_ptt_stage(
                'ptt_business_core.stage_ptt_proposal_sent',
                fallback_names=['Proposal', 'Proposition'],
                team=lead.team_id,
            )
            
            if proposal_stage and lead.stage_id != proposal_stage:
                lead.write({
                    'stage_id': proposal_stage.id,
                })
            
            # Mark proposal as sent on PTT lead fields
            if hasattr(lead, 'ptt_proposal_sent'):
                lead.ptt_proposal_sent = True
                
            # Log the action
            lead.message_post(
                body=_("Quotation %s sent to customer.") % order.name,
                message_type='notification',
            )
    
    def _update_crm_stage_on_contract_sent(self):
        """Update linked CRM lead stage when contract is sent.
        
        Finds the 'Contract Sent' stage and moves the lead to it.
        Also marks the ptt_contract_sent flag for tracking.
        """
        for order in self:
            lead = order.opportunity_id
            if not lead:
                continue
            
            contract_stage = self._get_ptt_stage(
                'ptt_business_core.stage_ptt_contract_sent',
                fallback_names=['Contract'],
                team=lead.team_id,
            )
            
            if contract_stage and lead.stage_id != contract_stage:
                lead.write({
                    'stage_id': contract_stage.id,
                })
            
            # Mark contract as sent on PTT lead fields
            if hasattr(lead, 'ptt_contract_sent'):
                lead.ptt_contract_sent = True
                
            # Log the action
            lead.message_post(
                body=_("Contract for %s sent to customer for signature.") % order.name,
                message_type='notification',
            )
    
    def action_send_contract(self):
        """Send contract to customer and update CRM stage.
        
        This method can be called from a button on the sale order form
        to send the formal contract and automatically update CRM pipeline.
        """
        self.ensure_one()
        self._update_crm_stage_on_contract_sent()
        # Mark that contract was sent on the order
        self.message_post(
            body=_("Contract sent to customer."),
            message_type='notification',
        )
        return True

    def _update_crm_stage_on_order_confirmed(self):
        """Update linked CRM lead when order is confirmed.
        
        Confirmed orders should move the opportunity to Booked.
        """
        for order in self:
            lead = order.opportunity_id
            if not lead:
                continue
            if lead.stage_id.is_won:
                continue
            booked_stage = self._get_ptt_stage(
                "crm.stage_lead4",  # Booked stage (was Won, renamed in crm_stages.xml)
                fallback_names=["Booked", "Won"],
                team=lead.team_id,
            )
            if booked_stage:
                lead.write({
                    "stage_id": booked_stage.id,
                    "probability": 100,
                })
            else:
                lead.action_set_won()
            if hasattr(lead, "ptt_booked"):
                lead.ptt_booked = True
            lead.message_post(
                body=_("Order %s confirmed.") % order.name,
                message_type='notification',
            )

    def _update_crm_stage_on_payment_confirmed(self, force=False):
        """Update linked CRM lead to 'Booked' (Won) stage when payment is confirmed."""
        for order in self:
            if not force and not order._ptt_is_fully_paid():
                continue
            lead = order.opportunity_id
            if not lead:
                continue
            if lead.stage_id.is_won:
                continue
            booked_stage = self._get_ptt_stage(
                'crm.stage_lead4',  # Booked stage (was Won, renamed in crm_stages.xml)
                fallback_names=['Booked', 'Won'],
                team=lead.team_id,
            )
            if booked_stage:
                lead.write({
                    'stage_id': booked_stage.id,
                    'probability': 100,
                })
            else:
                lead.action_set_won()
            if hasattr(lead, 'ptt_booked'):
                lead.ptt_booked = True
            lead.message_post(
                body=_("Payment confirmed for %s. Event is officially BOOKED!") % order.name,
                message_type='notification',
            )

    def _ptt_is_fully_paid(self):
        """Return True when all posted customer invoices are fully paid."""
        self.ensure_one()
        invoices = self.invoice_ids.filtered(lambda inv: inv.move_type == 'out_invoice' and inv.state == 'posted')
        return bool(invoices) and all(inv.payment_state == 'paid' for inv in invoices)
    
    def _sync_crm_lead_from_order(self):
        """DEPRECATED: Sync is now automatic via related fields.
        
        Event fields on sale.order are RELATED to opportunity_id (CRM Lead).
        Changes in SO automatically update CRM and vice versa.
        This method is kept for backward compatibility but does nothing.
        """
        pass  # Related fields handle sync automatically
    
    # Quote Management
    revision_count = fields.Integer(
        string="Revision Count",
        compute='_compute_revision_count',
        help="Number of revisions for this quote"
    )
    
    revision_ids = fields.One2many(
        'sale.order.revision',
        'original_order_id',
        string="Quote Revisions"
    )
    
    is_revision = fields.Boolean(
        string="Is Revision",
        default=False,
        help="True if this order is a revision of another"
    )
    
    original_order_id = fields.Many2one(
        'sale.order',
        string="Original Order",
        ondelete='set null',
        help="Original order if this is a revision"
    )
    
    current_revision_id = fields.Many2one(
        'sale.order',
        string="Current Revision",
        ondelete='set null',
        help="Most recent revision of this order"
    )
    
    @api.depends('revision_ids')
    def _compute_revision_count(self):
        """Compute number of quote revisions for this order."""
        for order in self:
            order.revision_count = len(order.revision_ids)
    
    @api.onchange('event_type')
    def _onchange_event_type(self):
        """Auto-add correct Event Kickoff product when event type is selected.
        
        Odoo 19 Reference:
        https://www.odoo.com/documentation/19.0/developer/reference/backend/orm.html#odoo.api.onchange
        
        Uses Command class for One2many manipulation (Odoo 19 standard):
        https://www.odoo.com/documentation/19.0/developer/reference/backend/orm.html#odoo.fields.Command
        """
        if not self.event_type:
            return
        
        # Auto-add the correct Event Kickoff product
        self._auto_add_event_kickoff_product()
    
    def _auto_add_event_kickoff_product(self):
        """Add or replace Event Kickoff product based on selected event type.
        
        This ensures:
        - The correct Event Kickoff product is always on the SO
        - It's always the first line item (sequence=0)
        - Only ONE Event Kickoff product exists at a time
        
        Odoo 19 Reference for onchange One2many manipulation:
        https://www.odoo.com/documentation/19.0/developer/reference/backend/orm.html#odoo.api.onchange
        
        In onchange context, we can directly modify the pseudo-records.
        """
        if not self.event_type:
            return
        
        # Get the correct Event Kickoff product code for this event type
        kickoff_code = EVENT_KICKOFF_PRODUCTS.get(self.event_type)
        if not kickoff_code:
            return
        
        # Find the Event Kickoff product (use product.product for variants)
        kickoff_product = self.env['product.product'].search([
            ('default_code', '=', kickoff_code),
            ('active', '=', True),
        ], limit=1)
        
        if not kickoff_product:
            # Product not found - may not be installed yet, skip silently
            return
        
        # Check existing lines for any Event Kickoff products
        existing_kickoff_line = None
        for line in self.order_line:
            if line.product_id and line.product_id.default_code in ALL_EVENT_KICKOFF_CODES:
                existing_kickoff_line = line
                break
        
        if existing_kickoff_line:
            # Already has an Event Kickoff - check if it's the correct one
            if existing_kickoff_line.product_id.default_code == kickoff_code:
                # Already correct, nothing to do
                return
            # Wrong Event Kickoff - update it to the correct one
            existing_kickoff_line.update({
                'product_id': kickoff_product.id,
                'name': kickoff_product.get_product_multiline_description_sale(),
                'product_uom_qty': 1.0,
                'sequence': 0,  # Keep as first line
            })
        else:
            # No Event Kickoff yet - add one as first line using new()
            # This is the Odoo 19 standard way to add lines in onchange
            new_line = self.env['sale.order.line'].new({
                'order_id': self.id,
                'product_id': kickoff_product.id,
                'name': kickoff_product.get_product_multiline_description_sale(),
                'product_uom_qty': 1.0,
                'price_unit': 0.0,  # Event Kickoff is $0
                'sequence': 0,  # First line
            })
            # Prepend to existing lines
            self.order_line = new_line | self.order_line

    def _add_event_kickoff_from_crm(self):
        """Add the correct Event Kickoff product when creating a quote from CRM.
        
        This is called programmatically (not via onchange) when a quotation
        is created from a CRM Lead that has an event type set.
        
        Unlike _auto_add_event_kickoff_product() which works with pseudo-records
        in onchange context, this method creates real sale.order.line records.
        
        Odoo 19 Reference:
        https://www.odoo.com/documentation/19.0/developer/reference/backend/orm.html#create
        """
        self.ensure_one()
        
        if not self.event_type:
            return
        
        # Get the correct Event Kickoff product code for this event type
        kickoff_code = EVENT_KICKOFF_PRODUCTS.get(self.event_type)
        if not kickoff_code:
            return
        
        # Find the Event Kickoff product
        kickoff_product = self.env['product.product'].search([
            ('default_code', '=', kickoff_code),
            ('active', '=', True),
        ], limit=1)
        
        if not kickoff_product:
            # Product not found - may not be installed yet, skip silently
            return
        
        # Check if an Event Kickoff already exists
        existing_kickoff = self.order_line.filtered(
            lambda l: l.product_id and l.product_id.default_code in ALL_EVENT_KICKOFF_CODES
        )
        
        if existing_kickoff:
            # Already has an Event Kickoff - check if it's the correct one
            if existing_kickoff[0].product_id.default_code == kickoff_code:
                return  # Already correct
            # Wrong Event Kickoff - update it
            existing_kickoff[0].write({
                'product_id': kickoff_product.id,
                'name': kickoff_product.get_product_multiline_description_sale(),
                'product_uom_qty': 1.0,
                'sequence': 0,
            })
        else:
            # Create a new line for the Event Kickoff product
            self.env['sale.order.line'].create({
                'order_id': self.id,
                'product_id': kickoff_product.id,
                'name': kickoff_product.get_product_multiline_description_sale(),
                'product_uom_qty': 1.0,
                'price_unit': 0.0,
                'sequence': 0,  # First line
            })
    
    def action_create_revision(self):
        """Create a new revision of this quote.
        
        Copies the current order as a new revision, maintaining
        the link to the original order for tracking purposes.
        
        Returns:
            dict: Action to open the new revision form.
        """
        self.ensure_one()
        
        # Determine the original order
        original = self.original_order_id or self
        
        # Copy the order
        revision = self.copy({
            'name': f"{original.name} - Rev {original.revision_count + 1}",
            'is_revision': True,
            'original_order_id': original.id,
            'state': 'draft',
        })
        
        # Create the revision tracking record
        self.env['sale.order.revision'].create({
            'name': f"Revision {original.revision_count + 1}",
            'original_order_id': original.id,
            'revised_order_id': revision.id,
            'revision_reason': f"Revision created from {self.name}",
        })
        
        # Update the current revision reference on the original
        original.current_revision_id = revision.id
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Revised Quote',
            'res_model': 'sale.order',
            'res_id': revision.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def action_view_revisions(self):
        """View all revisions of this quote"""
        revisions = self.revision_ids
        if self.original_order_id:
            revisions = self.original_order_id.revision_ids
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Quote Revisions',
            'res_model': 'sale.order',
            'view_mode': 'list,form',
            'domain': [('id', 'in', revisions.ids)],
            'target': 'current',
        }
    
    def action_create_project(self):
        """Create project from confirmed sale order with event-specific setup.
        
        In Odoo 19, super().action_create_project() opens a wizard dialog.
        We pass the CRM lead ID via context so the project is linked to the
        CRM lead, which enables automatic sync of all event details through
        related fields.
        
        NOTE: Event fields (ptt_event_type, ptt_event_name, ptt_event_date,
        ptt_venue_name, etc.) are RELATED to CRM Lead fields on project.
        They cannot be written directly - link to CRM lead instead.
        """
        action = super().action_create_project()
        
        # Pass CRM lead ID via context for project creation
        # This enables all event fields to sync via related fields
        if isinstance(action, dict) and action.get('context'):
            event_context = {
                'default_ptt_crm_lead_id': self.opportunity_id.id if self.opportunity_id else False,
            }
            action['context'] = {**action.get('context', {}), **event_context}
        
        return action
    
    def _apply_event_details_to_project(self, project):
        """Link project to CRM lead for event detail sync.
        
        Event details (event type, name, date, venue, etc.) are stored on the
        CRM Lead and displayed as related/readonly fields on the project.
        
        This method links the project to the CRM lead (via opportunity_id),
        which automatically syncs all event details through the related fields.
        
        NOTE: Do NOT write directly to project event fields - they are related
        to ptt_crm_lead_id and are readonly. Update the CRM lead instead.
        """
        if not project:
            return
        
        # Link project to CRM Lead - this is what enables the related field sync
        # All event fields (ptt_event_type, ptt_event_name, ptt_event_date,
        # ptt_venue_name, ptt_guest_count, etc.) are RELATED to CRM Lead fields.
        # Writing them directly to project won't work - they're readonly.
        if self.opportunity_id and not project.ptt_crm_lead_id:
            project.write({'ptt_crm_lead_id': self.opportunity_id.id})
        
        # Note: Task creation is now handled in sale_order_line.py 
        # via _timesheet_create_project() when Event Kickoff product creates the project


class SaleOrderRevision(models.Model):
    """Track revisions of sale orders for event quotes"""
    _name = 'sale.order.revision'
    _description = 'Sale Order Revision History'
    _order = 'revision_date desc'
    
    name = fields.Char(
        string="Revision Name",
        required=True
    )
    
    original_order_id = fields.Many2one(
        'sale.order',
        string="Original Order",
        required=True,
        ondelete='cascade'
    )
    
    revised_order_id = fields.Many2one(
        'sale.order',
        string="Revised Order",
        required=True,
        ondelete='cascade'
    )
    
    revision_date = fields.Datetime(
        string="Revision Date",
        default=fields.Datetime.now,
        required=True
    )
    
    revision_reason = fields.Text(
        string="Reason for Revision",
        help="Explanation of why this revision was created"
    )
    
    user_id = fields.Many2one(
        'res.users',
        string="Revised By",
        default=lambda self: self.env.user,
        required=True
    )
