from odoo import models, fields, api, _


class SaleOrder(models.Model):
    """Extend Sale Order with PTT contract tracking and project creation.
    
    Note: Quote approval is handled via CRM Approval stage.
    Note: Retainer/payment calculations are handled by Finance team.
    
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

    def action_confirm(self):
        """Override to create project when Sales Order is confirmed.
        
        Workflow:
        1. Confirm the Sales Order (standard Odoo behavior)
        2. Generate Event ID on CRM Lead (if not already set)
        3. Create Project from CRM Lead (inherits Event ID)
        4. Project creation triggers task creation (tasks inherit Event ID)
        5. Move CRM to Booked stage
        """
        res = super().action_confirm()
        
        for order in self:
            # Only process if order is now confirmed (state='sale')
            if order.state == 'sale' and order.opportunity_id:
                lead = order.opportunity_id
                
                # STEP 1: Generate Event ID on CRM Lead FIRST (before project creation)
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
                        continue  # Skip project creation if Event ID fails
                
                # STEP 2: Create project if it doesn't exist yet
                if not lead.x_project_id:
                    try:
                        lead.action_create_project_from_lead()
                        lead.message_post(
                            body=_("Project automatically created: Sales Order confirmed."),
                            message_type="notification",
                        )
                    except Exception as e:
                        # Log error but don't break the confirmation process
                        lead.message_post(
                            body=_("Error creating project: %s") % str(e),
                            message_type="notification",
                            subtype_xmlid="mail.mt_note",
                        )
                
                # STEP 3: Move CRM to Booked stage
                booked_stage = self.env["crm.stage"].search(
                    [("name", "=", "Booked")], limit=1
                )
                if booked_stage and lead.stage_id != booked_stage:
                    lead.stage_id = booked_stage.id
                    lead.message_post(
                        body=_("Automatically moved to Booked: Sales Order confirmed."),
                        message_type="notification",
                    )
        
        return res

    def action_mark_contract_signed(self):
        """Mark contract as signed."""
        self.ensure_one()
        self.write({
            "x_contract_status": "signed",
            "x_contract_signed_date": fields.Datetime.now(),
        })
        return True
