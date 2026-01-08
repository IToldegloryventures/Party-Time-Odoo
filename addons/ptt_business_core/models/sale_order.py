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
        2. Generate Event ID on CRM Lead
        3. Create Event Project with tasks
        4. Move CRM to 'Booked' stage
        
        This is the KEY trigger for project creation.
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
                
                # Process CRM opportunity if linked
                if order.opportunity_id:
                    lead = order.opportunity_id
                    
                    # STEP 1: Generate Event ID on CRM Lead
                    if not lead.x_event_id:
                        try:
                            lead._generate_event_id()
                            lead.message_post(
                                body=_("Event ID generated: %s") % lead.x_event_id,
                                message_type="notification",
                            )
                        except Exception as e:
                            lead.message_post(
                                body=_("Error generating Event ID: %s") % str(e),
                                message_type="notification",
                                subtype_xmlid="mail.mt_note",
                            )
                    
                    # STEP 2: Create Event Project if it doesn't exist
                    if not lead.x_project_id:
                        try:
                            lead.action_create_project_from_lead()
                            lead.message_post(
                                body=_("Event Project created: Contract accepted."),
                                message_type="notification",
                            )
                        except Exception as e:
                            lead.message_post(
                                body=_("Error creating project: %s") % str(e),
                                message_type="notification",
                                subtype_xmlid="mail.mt_note",
                            )
                    
                    # STEP 3: Move CRM to Booked stage
                    self._update_crm_stage(
                        "Booked",
                        _("CRM stage updated to Booked: Customer accepted contract.")
                    )
        
        return res
