from odoo import models, fields, api, _


class SaleOrder(models.Model):
    """Extend Sale Order with PTT CRM stage automation.
    
    CRM Stage Workflow:
    1. Quote/Proposal Sent → CRM moves to "Proposal Sent"
    2. Customer Accepts (SO Confirmed) → CRM moves to "Booked"
    
    NOTE: Contract status = Use standard 'state' field (draft/sent/sale)
    NOTE: Contract signed date = Use standard 'date_order' when state='sale'
    
    Per Odoo 19 Sales docs: https://www.odoo.com/documentation/19.0/applications/sales/sales.html
    """
    _inherit = "sale.order"

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
