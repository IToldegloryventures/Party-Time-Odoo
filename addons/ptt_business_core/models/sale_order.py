from odoo import models, fields, api, _


class SaleOrder(models.Model):
    """Extend Sale Order with PTT contract tracking and CRM stage automation.
    
    CRM Stage Workflow:
    1. Quote/Proposal Sent → CRM moves to "Proposal Sent"
    2. Customer Accepts (SO Confirmed) = Contract Signed → Project Created + CRM moves to "Booked"
    
    The Sales Order IS the contract - when customer accepts/confirms, that's the signature.
    
    Per Odoo 19 Sales docs: https://www.odoo.com/documentation/19.0/applications/sales/sales.html
    """
    _inherit = "sale.order"

    # === CONTRACT STATUS (auto-updated based on SO state) ===
    x_contract_status = fields.Selection(
        [
            ("not_sent", "Not Sent"),
            ("sent", "Sent to Customer"),
            ("signed", "Signed/Accepted"),
        ],
        string="Contract Status",
        compute="_compute_contract_status",
        store=True,
        tracking=True,
        help="Contract status based on Sales Order state. Sent = Quote sent, Signed = SO confirmed (customer accepted).",
    )
    x_contract_signed_date = fields.Datetime(
        string="Contract Signed Date",
        readonly=True,
    )

    @api.depends("state")
    def _compute_contract_status(self):
        """Auto-compute contract status based on SO state.
        
        - Draft → Not Sent
        - Sent → Sent to Customer  
        - Sale (confirmed) → Signed/Accepted
        """
        for order in self:
            if order.state == 'sale':
                order.x_contract_status = 'signed'
            elif order.state == 'sent':
                order.x_contract_status = 'sent'
            else:
                order.x_contract_status = 'not_sent'

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
        The quote IS the contract/proposal being sent to customer.
        """
        res = super().action_quotation_sent()
        self._update_crm_stage(
            "Proposal Sent",
            _("CRM stage updated: Quote/Contract sent to customer for review.")
        )
        return res

    def action_confirm(self):
        """Override SO confirmation - Customer accepted = Contract signed.
        
        When SO is confirmed (customer accepts):
        1. Mark contract as signed with timestamp
        2. Move CRM to 'Booked' stage
        3. Auto-create vendor assignments from CRM estimates (if project exists)
        
        Note: Project creation is handled MANUALLY in Odoo, not automatically here.
        """
        res = super().action_confirm()
        
        for order in self:
            # Only process if order is now confirmed (state='sale')
            if order.state == 'sale':
                # Record the contract signed date
                if not order.x_contract_signed_date:
                    order.write({"x_contract_signed_date": fields.Datetime.now()})
                
                order.message_post(
                    body=_("Contract accepted by customer."),
                    message_type="notification",
                )
                
                # Move CRM to Booked stage (if linked to opportunity)
                if order.opportunity_id:
                    self._update_crm_stage(
                        "Booked",
                        _("CRM stage updated to Booked: Customer accepted contract.")
                    )
                    
                    # Auto-create vendor assignments from CRM estimates
                    self._create_vendor_assignments_from_estimates(order)
        
        return res
    
    def _create_vendor_assignments_from_estimates(self, order):
        """Create vendor assignments from CRM estimates when SO is confirmed.
        
        This creates vendor assignments on the project (if it exists) based on
        the vendor estimates from the CRM opportunity.
        """
        if not order.opportunity_id:
            return
        
        # Find project linked to this opportunity
        project = self.env["project.project"].search([
            ("x_crm_lead_id", "=", order.opportunity_id.id)
        ], limit=1)
        
        if not project:
            # Project not created yet - assignments will be created when project is created
            return
        
        # Get vendor estimates from CRM opportunity
        estimates = order.opportunity_id.x_vendor_estimate_ids
        
        if not estimates:
            return
        
        # Create vendor assignments for each estimate
        VendorAssignment = self.env["ptt.project.vendor.assignment"]
        
        for estimate in estimates:
            # Check if assignment already exists
            existing = VendorAssignment.search([
                ("project_id", "=", project.id),
                ("service_type", "=", estimate.service_type),
            ], limit=1)
            
            if existing:
                continue  # Skip if already exists
            
            # Create assignment
            assignment_vals = {
                "project_id": project.id,
                "service_type": estimate.service_type,
                "estimated_cost": estimate.estimated_cost,
                "x_status": "pending",
            }
            
            # Link to vendor if specified
            if estimate.vendor_id:
                assignment_vals["vendor_id"] = estimate.vendor_id.id
            
            VendorAssignment.create(assignment_vals)
        
        if estimates:
            project.message_post(
                body=_("Vendor assignments created from CRM estimates."),
                message_type="notification",
            )

    # === NAVIGATION ACTIONS ===
    
    def action_view_opportunity(self):
        """Navigate to the linked CRM Opportunity."""
        self.ensure_one()
        if not self.opportunity_id:
            return False
        return {
            "type": "ir.actions.act_window",
            "name": _("CRM Opportunity"),
            "res_model": "crm.lead",
            "res_id": self.opportunity_id.id,
            "view_mode": "form",
            "target": "current",
        }
