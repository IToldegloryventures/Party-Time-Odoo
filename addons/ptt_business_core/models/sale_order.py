from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    """Extend Sale Order with PTT quote approval workflow and retainer calculation.
    
    Per Odoo 19 Sales docs: https://www.odoo.com/documentation/19.0/applications/sales/sales.html
    """
    _inherit = "sale.order"

    # === QUOTE APPROVAL WORKFLOW ===
    x_is_approved = fields.Boolean(
        string="Approved",
        default=False,
        tracking=True,
        help="Quote must be approved before it can be sent to client.",
    )
    x_approved_by = fields.Many2one(
        "res.users",
        string="Approved By",
        readonly=True,
        help="User who approved this quote.",
    )
    x_approved_date = fields.Datetime(
        string="Approval Date",
        readonly=True,
        help="Date and time the quote was approved.",
    )

    # === RETAINER CALCULATION ===
    x_retainer_amount = fields.Monetary(
        string="Required Retainer",
        compute="_compute_retainer_amount",
        store=True,
        currency_field="currency_id",
        help="Retainer required: 10% of total or $500 minimum (whichever is greater).",
    )

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

    # === RETAINER PAYMENT STATUS ===
    x_retainer_paid = fields.Boolean(
        string="Retainer Paid",
        default=False,
        tracking=True,
        help="Check when retainer payment has been received.",
    )
    x_retainer_paid_date = fields.Date(
        string="Retainer Paid Date",
    )

    @api.depends("amount_total")
    def _compute_retainer_amount(self):
        """Calculate retainer: 10% or $500 minimum (whichever is greater)."""
        for order in self:
            ten_percent = order.amount_total * 0.10
            order.x_retainer_amount = max(ten_percent, 500.0)

    def action_approve_quote(self):
        """Approve the quote. Only users in Quote Approver group can do this."""
        self.ensure_one()
        if self.x_is_approved:
            raise UserError(_("This quote is already approved."))
        
        self.write({
            "x_is_approved": True,
            "x_approved_by": self.env.user.id,
            "x_approved_date": fields.Datetime.now(),
        })
        
        # Log approval in chatter
        self.message_post(
            body=_("Quote approved by %s") % self.env.user.name,
            message_type="notification",
        )
        
        return True

    def action_send_quotation(self):
        """Override to check approval before sending quote to client."""
        self.ensure_one()
        if not self.x_is_approved:
            raise UserError(_(
                "This quote requires approval before it can be sent.\n"
                "Please have a Quote Approver approve this quote first."
            ))
        return super().action_send_quotation()

    def action_confirm(self):
        """Override to create project when Sales Order is confirmed."""
        res = super().action_confirm()
        
        for order in self:
            # Only process if order is now confirmed (state='sale')
            if order.state == 'sale' and order.opportunity_id:
                # Auto-create project if it doesn't exist yet
                if not order.opportunity_id.x_project_id:
                    try:
                        order.opportunity_id.action_create_project_from_lead()
                        order.opportunity_id.message_post(
                            body=_("Project automatically created: Sales Order confirmed."),
                            message_type="notification",
                        )
                        # Move CRM to Booked stage
                        booked_stage = self.env["crm.stage"].search(
                            [("name", "=", "Booked")], limit=1
                        )
                        if booked_stage and order.opportunity_id.stage_id != booked_stage:
                            order.opportunity_id.stage_id = booked_stage.id
                            order.opportunity_id.message_post(
                                body=_("Automatically moved to Booked: Sales Order confirmed."),
                                message_type="notification",
                            )
                    except Exception as e:
                        # Log error but don't break the confirmation process
                        order.opportunity_id.message_post(
                            body=_("Error creating project: %s") % str(e),
                            message_type="notification",
                            subtype_xmlid="mail.mt_note",
                        )
        
        return res

    def action_mark_contract_signed(self):
        """Mark contract as signed and check if we should advance CRM stage."""
        self.ensure_one()
        self.write({
            "x_contract_status": "signed",
            "x_contract_signed_date": fields.Datetime.now(),
        })
        self._check_booking_complete()
        return True

    def action_mark_retainer_paid(self):
        """Mark retainer as paid and check if we should advance CRM stage."""
        self.ensure_one()
        self.write({
            "x_retainer_paid": True,
            "x_retainer_paid_date": fields.Date.today(),
        })
        self._check_booking_complete()
        return True

    def _check_booking_complete(self):
        """Check if contract signed AND retainer paid, then advance CRM to Booked stage.
        
        Note: Project is now created when Sales Order is confirmed (in action_confirm),
        so this method only handles moving to Booked stage when contract is signed and retainer paid.
        """
        self.ensure_one()
        if self.x_contract_status == "signed" and self.x_retainer_paid:
            # Find linked CRM lead via opportunity_id (standard Odoo field)
            if self.opportunity_id:
                # Find the "Booked" stage
                booked_stage = self.env["crm.stage"].search(
                    [("name", "=", "Booked")], limit=1
                )
                if booked_stage and self.opportunity_id.stage_id != booked_stage:
                    self.opportunity_id.stage_id = booked_stage.id
                    self.opportunity_id.message_post(
                        body=_("Automatically moved to Booked: Contract signed and retainer paid."),
                        message_type="notification",
                    )