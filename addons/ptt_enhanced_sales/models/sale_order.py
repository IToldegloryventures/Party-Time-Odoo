# Part of Party Time Texas Event Management System
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import models, fields, api, _

from odoo.addons.ptt_business_core.constants import LOCATION_TYPES


class SaleOrder(models.Model):
    """Enhanced Sale Order for Event Management"""
    _inherit = 'sale.order'

    # Event Type Classification
    event_type_id = fields.Many2one(
        'sale.order.type',
        string="Event Type",
        help="Type of event for this order (Corporate/Social/Wedding)"
    )
    
    # NOTE: Category field removed - event type name (Corporate/Social/Wedding) is the category
    
    # Event Details
    event_name = fields.Char(
        string="Event Name",
        help="Name of the specific event"
    )
    
    event_date = fields.Datetime(
        string="Event Date & Time",
        help="Scheduled date and time of the event"
    )
    
    event_duration = fields.Float(
        string="Event Duration (Hours)",
        help="Duration of the event in hours"
    )
    
    event_guest_count = fields.Integer(
        string="Expected Guest Count",
        help="Number of expected guests"
    )
    
    event_venue = fields.Char(
        string="Event Venue",
        help="Location where the event will take place"
    )
    
    event_venue_type = fields.Selection(
        selection=LOCATION_TYPES,
        string="Venue Type"
    )
    
    # Setup and Breakdown
    setup_time = fields.Datetime(
        string="Setup Start Time",
        help="When setup should begin"
    )
    
    breakdown_time = fields.Datetime(
        string="Breakdown Time",
        help="When breakdown should be completed"
    )
    
    # Services Required (from Event Type)
    service_dj = fields.Boolean(
        string="DJ/MC Services",
        help="DJ and MC services required"
    )
    service_photo = fields.Boolean(
        string="Photo/Video Services", 
        help="Photography/videography services required"
    )
    service_live = fields.Boolean(
        string="Live Entertainment",
        help="Live entertainment (bands, musicians) required"
    )
    service_lighting = fields.Boolean(
        string="Lighting/AV Services",
        help="Lighting and AV services required"
    )
    service_decor = fields.Boolean(
        string="Decor & Theming",
        help="Decoration and theming services required"
    )
    service_photobooth = fields.Boolean(
        string="Photo Booth Rental",
        help="Photo booth services required"
    )
    service_casino = fields.Boolean(
        string="Casino Services",
        help="Casino entertainment services required"
    )
    service_staffing = fields.Boolean(
        string="Event Staffing",
        help="Additional event staffing required"
    )

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
        """Sync event details from sale order back to CRM lead.
        
        Useful when order details are updated after initial creation.
        Updates the linked opportunity with current event information.
        """
        for order in self:
            lead = order.opportunity_id
            if not lead:
                continue
            
            sync_vals = {}
            
            if order.event_name and lead.ptt_event_name != order.event_name:
                sync_vals['ptt_event_name'] = order.event_name
            if order.event_date:
                order_event_date = order.event_date.date() if hasattr(order.event_date, 'date') else order.event_date
                if lead.ptt_event_date != order_event_date:
                    sync_vals['ptt_event_date'] = order_event_date
            if order.event_guest_count and lead.ptt_guest_count != order.event_guest_count:
                sync_vals['ptt_guest_count'] = order.event_guest_count
            if order.event_venue and lead.ptt_venue_name != order.event_venue:
                sync_vals['ptt_venue_name'] = order.event_venue
            
            if sync_vals:
                lead.write(sync_vals)
    
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
    
    @api.onchange('event_type_id')
    def _onchange_event_type_id(self):
        """Auto-populate services and duration based on event type.
        
        Copies default service flags and duration hours from the
        selected event type template.
        """
        if self.event_type_id:
            self.service_dj = self.event_type_id.default_service_dj
            self.service_photo = self.event_type_id.default_service_photo
            self.service_live = self.event_type_id.default_service_live
            self.service_lighting = self.event_type_id.default_service_lighting
            self.service_decor = self.event_type_id.default_service_decor
            self.service_photobooth = self.event_type_id.default_service_photobooth
            self.service_casino = self.event_type_id.default_service_casino
            self.service_staffing = self.event_type_id.default_service_staffing
            
            # Set default duration
            if self.event_type_id.default_duration_hours:
                self.event_duration = self.event_type_id.default_duration_hours
    
    @api.onchange('event_date', 'event_type_id')
    def _onchange_event_timing(self):
        """Auto-calculate setup and breakdown times.
        
        Uses event type defaults to calculate:
        - setup_time: Event date minus setup hours
        - breakdown_time: Event end plus breakdown hours
        """
        if self.event_date and self.event_type_id:
            # Calculate setup time
            if self.event_type_id.default_setup_hours:
                setup_hours = self.event_type_id.default_setup_hours
                self.setup_time = fields.Datetime.subtract(
                    self.event_date, 
                    hours=setup_hours
                )
            
            # Calculate breakdown time
            if self.event_type_id.default_breakdown_hours and self.event_duration:
                breakdown_hours = self.event_type_id.default_breakdown_hours
                event_end = fields.Datetime.add(
                    self.event_date,
                    hours=self.event_duration
                )
                self.breakdown_time = fields.Datetime.add(
                    event_end,
                    hours=breakdown_hours
                )
    
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
            'view_mode': 'tree,form',
            'domain': [('id', 'in', revisions.ids)],
            'target': 'current',
        }
    
    def action_create_project(self):
        """Create project from confirmed sale order with event-specific setup.
        
        In Odoo 19, super().action_create_project() opens a wizard dialog.
        We pass event data via context so it can be used when the project
        is actually created by the wizard or linked to the sale order.
        """
        action = super().action_create_project()
        
        # Pass event details via context for project creation
        if isinstance(action, dict) and action.get('context'):
            event_context = {
                'ptt_event_type_id': self.event_type_id.id if self.event_type_id else False,
                'ptt_event_name': self.event_name,
                'ptt_guest_count': self.event_guest_count,
                'ptt_venue_name': self.event_venue,
                'ptt_setup_start_time': self.setup_time,
                'ptt_teardown_deadline': self.breakdown_time,
                'ptt_total_hours': self.event_duration,
                'ptt_sale_order_id': self.id,
            }
            if self.event_date:
                event_context['ptt_event_date'] = self.event_date.date() if hasattr(self.event_date, 'date') else self.event_date
                event_context['ptt_event_start_time'] = self.event_date
            
            action['context'] = {**action.get('context', {}), **event_context}
        
        return action
    
    def _apply_event_details_to_project(self, project):
        """Apply event details from sale order to linked project.
        
        This method is called when a project is linked to the sale order,
        typically after project creation via wizard or direct linking.
        """
        if not project or not self.event_type_id:
            return
            
        project_vals = {
            'ptt_event_type_id': self.event_type_id.id,
            'ptt_event_name': self.event_name,
            'ptt_guest_count': self.event_guest_count,
            'ptt_venue_name': self.event_venue,
            'ptt_setup_start_time': self.setup_time,
            'ptt_teardown_deadline': self.breakdown_time,
            'ptt_total_hours': self.event_duration,
        }
        
        # Handle event_date (Datetime) -> ptt_event_date (Date) conversion
        if self.event_date:
            project_vals['ptt_event_date'] = self.event_date.date() if hasattr(self.event_date, 'date') else self.event_date
            project_vals['ptt_event_start_time'] = self.event_date
            if self.event_duration:
                project_vals['ptt_event_end_time'] = fields.Datetime.add(self.event_date, hours=self.event_duration)
        
        project.write(project_vals)
        
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
