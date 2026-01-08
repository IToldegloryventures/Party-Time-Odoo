from odoo import models, fields, api, _


class SaleOrder(models.Model):
    """Extend Sale Order with PTT contract tracking and CRM stage automation.
    
    CRM Stage Workflow:
    1. Quote/Proposal Sent → CRM moves to "Proposal Sent"
    2. Contract Sent → CRM moves to "Contract Sent"
    3. Contract Signed → Event Project Created + CRM moves to "Booked"
    
    Per Odoo 19 Sales docs: https://www.odoo.com/documentation/19.0/applications/sales/sales.html
    """
    _inherit = "sale.order"

    # === CONTRACT STATUS ===
    x_contract_status = fields.Selection(
        [
            ("not_sent", "Not Sent"),
            ("sent", "Sent for Signature"),
            ("signed", "Signed"),
        ],
        string="Contract Status",
        default="not_sent",
        tracking=True,
        help="Track contract signature status.",
    )
    x_contract_signed_date = fields.Datetime(
        string="Contract Signed Date",
        readonly=True,
    )

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
        """Override: When quote/proposal is sent, update CRM to 'Proposal Sent'."""
        res = super().action_quotation_sent()
        self._update_crm_stage(
            "Proposal Sent",
            _("CRM stage updated: Proposal/Quote sent to client.")
        )
        return res

    def action_send_contract(self):
        """Send contract to client for signature.
        
        Updates contract status to 'sent' and moves CRM to 'Contract Sent' stage.
        """
        for order in self:
            order.write({"x_contract_status": "sent"})
            order.message_post(
                body=_("Contract sent for signature."),
                message_type="notification",
            )
        
        self._update_crm_stage(
            "Contract Sent",
            _("CRM stage updated: Contract sent for signature.")
        )
        return True

    def action_mark_contract_signed(self):
        """Mark contract as signed - triggers project creation and CRM to 'Booked'.
        
        This is the KEY action that:
        1. Marks the contract as signed
        2. Confirms the Sales Order (if not already confirmed)
        3. Generates the Event ID on CRM Lead
        4. Creates the Event Project
        5. Moves CRM to 'Booked' stage
        """
        for order in self:
            # Mark contract as signed
            order.write({
                "x_contract_status": "signed",
                "x_contract_signed_date": fields.Datetime.now(),
            })
            order.message_post(
                body=_("Contract signed by client."),
                message_type="notification",
            )
            
            # Confirm the SO if not already confirmed
            if order.state in ('draft', 'sent'):
                order.action_confirm()
            
            # Now create the project (if linked to opportunity)
            if order.opportunity_id:
                lead = order.opportunity_id
                
                # Generate Event ID if not already set
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
                
                # Create project if it doesn't exist yet
                if not lead.x_project_id:
                    try:
                        lead.action_create_project_from_lead()
                        lead.message_post(
                            body=_("Event Project created: Contract signed."),
                            message_type="notification",
                        )
                    except Exception as e:
                        lead.message_post(
                            body=_("Error creating project: %s") % str(e),
                            message_type="notification",
                            subtype_xmlid="mail.mt_note",
                        )
        
        # Move CRM to Booked
        self._update_crm_stage(
            "Booked",
            _("CRM stage updated to Booked: Contract signed.")
        )
        return True

    def write(self, vals):
        """Override write to handle contract status changes.
        
        Automatically updates CRM stage when x_contract_status changes.
        """
        res = super().write(vals)
        
        # Handle contract status changes
        if "x_contract_status" in vals:
            new_status = vals["x_contract_status"]
            
            if new_status == "sent":
                # Contract sent → CRM to "Contract Sent"
                self._update_crm_stage(
                    "Contract Sent",
                    _("CRM stage updated: Contract sent for signature.")
                )
            elif new_status == "signed":
                # Contract signed → handled by action_mark_contract_signed
                # But if someone sets it directly via write, still update CRM
                for order in self:
                    if order.opportunity_id:
                        lead = order.opportunity_id
                        
                        # Generate Event ID and create project if needed
                        if not lead.x_event_id:
                            try:
                                lead._generate_event_id()
                            except Exception:
                                pass
                        
                        if not lead.x_project_id and lead.x_event_id:
                            try:
                                lead.action_create_project_from_lead()
                            except Exception:
                                pass
                
                self._update_crm_stage(
                    "Booked",
                    _("CRM stage updated to Booked: Contract signed.")
                )
        
        return res

    def action_confirm(self):
        """Override SO confirmation - standard behavior only.
        
        Note: Project creation is NOT triggered here anymore.
        Project creation happens when contract is SIGNED (action_mark_contract_signed).
        """
        return super().action_confirm()
