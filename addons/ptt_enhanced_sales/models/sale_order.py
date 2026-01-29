# Part of Party Time Texas Event Management System
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import models, fields, api, _

from odoo.addons.ptt_business_core.constants import LOCATION_TYPES



class SaleOrder(models.Model):
    """Enhanced Sale Order for Event Management"""
    _inherit = 'sale.order'

    # Client Initials for Terms Acceptance (Portal)
    ptt_client_initials = fields.Char(
        string="Client Initials (Terms Acceptance)",
        help="Customer must enter initials to acknowledge Terms and Conditions before confirming the order via portal."
    )

    # Event Type Classification
    event_type_id = fields.Many2one(
        'sale.order.type',
        string="Event Type",
        help="Type of event for this order (Corporate/Social/Wedding)"
    )
    sale_order_template_id = fields.Many2one(
        'sale.order.template',
        string="Quotation Template",
        help="Auto-selected from the event type's default quotation template.",
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
        related="opportunity_id.ptt_event_duration",
        store=True,
        readonly=False,
        help="Duration of the event in hours (sourced from linked CRM opportunity)."
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
    
    event_venue_address = fields.Text(
        string="Venue Address",
        help="Full address of the venue"
    )
    
    event_venue_booked = fields.Boolean(
        string="Venue Booked?",
        help="Is the venue already booked/confirmed?"
    )
    
    event_attire = fields.Selection(
        selection=[
            ('casual', 'Casual'),
            ('business_casual', 'Business Casual'),
            ('semi_formal', 'Semi-Formal'),
            ('formal', 'Formal'),
            ('black_tie', 'Black Tie'),
            ('costume', 'Costume/Theme'),
            ('other', 'Other'),
        ],
        string="Attire/Dress Code",
        help="Dress code for the event"
    )
    
    # =========================================================================
    # EVENT TIMES - Using Datetime fields with proper date/time pickers
    # =========================================================================
    # NOTE: event_date (Datetime) is the EVENT START date+time
    # These are proper Datetime fields with date/time pickers (no confusing floats!)
    
    event_end_datetime = fields.Datetime(
        string="Event End Time",
        help="When the event ends"
    )
    
    setup_time = fields.Datetime(
        string="Setup Start Time",
        help="When setup should begin"
    )
    
    breakdown_time = fields.Datetime(
        string="Breakdown/Strike Time",
        help="When breakdown should be completed"
    )
    
    # Legacy Float fields (kept for backward compatibility with CRM sync)
    # These are NOT shown on the form - only Datetime fields are shown
    event_start_time = fields.Float(
        string="Start Time (Float)",
        help="Legacy: Event start time as float hours"
    )
    
    event_end_time = fields.Float(
        string="End Time (Float)", 
        help="Legacy: Event end time as float hours"
    )
    
    setup_time_float = fields.Float(
        string="Setup Time (Float)",
        help="Legacy: Setup time as float hours"
    )
    
    # =========================================================================
    # EVENT DETAILS SUMMARY (For Customer-Facing Documents)
    # =========================================================================
    event_details_summary = fields.Text(
        string="Event Details Summary",
        compute="_compute_event_details_summary",
        store=False,
        help="Formatted summary of event details for quotes and contracts"
    )
    
    @api.depends('event_name', 'event_type_id', 'event_date', 'event_end_datetime',
                 'event_guest_count', 'event_venue', 'event_venue_address', 
                 'event_attire', 'setup_time', 'event_duration')
    def _compute_event_details_summary(self):
        """Generate a formatted summary of event details for customer documents."""
        for order in self:
            lines = []
            
            if order.event_name:
                lines.append(f"Event: {order.event_name}")
            if order.event_type_id:
                lines.append(f"Type: {order.event_type_id.name}")
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
        """Confirm order and update CRM stage (native project creation only)."""
        result = super().action_confirm()
        # After native project/task creation, align all service lines to one project
        self._ensure_single_event_project()
        # Copy service task templates (or create simple tasks) into the event project
        self._create_service_tasks_from_templates()
        self._update_crm_stage_on_order_confirmed()
        return result

    # ---------------------------------------------------------------------
    # Project alignment: keep all service lines under the same event project
    # ---------------------------------------------------------------------
    def _ensure_single_event_project(self):
        """Create/assign one project for the order and link all service lines.

        - Use the first service line tracked as 'project_only' (Event Kickoff)
          as the project master; Odoo's native confirm already creates the
          project + template tasks for that line.
        - Any other service lines without a project_id are pointed to this
          project so their tasks fall under the same parent project.
        """
        for order in self:
            # Identify the kickoff line that should create the project
            kickoff_line = order.order_line.filtered(
                lambda l: l.product_id
                and l.product_id.type == 'service'
                and l.product_id.service_tracking == 'project_only'
            )[:1]

            project = kickoff_line.project_id if kickoff_line else False
            if not project:
                project = order.order_line.mapped('project_id')[:1]

            # Push the project to every service line that lacks one
            if project:
                service_lines = order.order_line.filtered(
                    lambda l: l.product_id
                    and l.product_id.type == 'service'
                    and not l.project_id
                )
                if service_lines:
                    service_lines.write({'project_id': project.id})

    def _create_service_tasks_from_templates(self):
        """For each service line, copy its task template into the event project.

        - Templates live in a dedicated project (created in post_init_hook)
          and are tagged with ptt_service_product_id = product variant.
        - If no template exists for a service, create a simple task named after
          the sale line/product.
        """
        template_project = self.env.ref(
            "ptt_enhanced_sales.service_task_template_project", raise_if_not_found=False
        )
        if not template_project:
            return

        for order in self:
            # use the project created by Event Kickoff (or first project on lines)
            project = order.order_line.mapped("project_id")[:1]
            if not project:
                continue

            for line in order.order_line.filtered(
                lambda l: l.product_id and l.product_id.type == "service" and l.product_id != False
            ):
                # Skip kickoff/project-only lines; they already created template tasks
                if line.product_id.service_tracking == "project_only":
                    continue

                templates = self.env["project.task"].search([
                    ("project_id", "=", template_project.id),
                    ("ptt_service_product_id", "=", line.product_id.id),
                ])

                if templates:
                    for tmpl in templates:
                        tmpl.copy({
                            "project_id": project.id,
                            "name": line.name or line.product_id.display_name,
                        })
                else:
                    self.env["project.task"].create({
                        "name": line.name or line.product_id.display_name,
                        "project_id": project.id,
                    })

    @api.onchange('event_type_id')
    def _onchange_event_type_id_templates(self):
        """Auto-apply quotation template from event type."""
        if self.event_type_id and self.event_type_id.quotation_template_id:
            self.sale_order_template_id = self.event_type_id.quotation_template_id
    
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
        """Event type no longer sets duration/setup/breakdown."""
        return
    
    @api.onchange('event_date', 'event_type_id')
    def _onchange_event_timing(self):
        """No automatic timing from event type; user sets times explicitly."""
        return
    
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
        
        # Note: Task/project creation now relies on native Odoo flows.

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
