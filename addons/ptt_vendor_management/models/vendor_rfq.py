# Part of Party Time Texas Event Management System
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
"""
Vendor RFQ (Request for Quote) Model.

Allows sending quote requests to multiple vendors for event services.
Vendors can respond via portal with pricing and availability.
Inspired by Cybrosys Technologies vendor_portal_odoo module.
"""

from odoo import api, fields, models, _
from odoo.exceptions import UserError

# Import service types from business core
from odoo.addons.ptt_business_core.constants import SERVICE_TYPES


class PttVendorRfq(models.Model):
    """Vendor RFQ for event services."""
    _name = "ptt.vendor.rfq"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Vendor Request for Quote"
    _order = "create_date desc"

    _positive_estimated_budget = models.Constraint(
        "CHECK (estimated_budget >= 0)",
        "Estimated budget cannot be negative.",
    )
    _positive_guest_count = models.Constraint(
        "CHECK (guest_count >= 0)",
        "Guest count cannot be negative.",
    )

    name = fields.Char(
        string="RFQ Reference",
        required=True,
        index=True,
        copy=False,
        default=lambda self: _("New"),
    )
    
    # Link to CRM Lead or Project
    crm_lead_id = fields.Many2one(
        "crm.lead",
        string="Related Lead",
        index=True,
        help="CRM Lead this RFQ is for",
    )
    project_id = fields.Many2one(
        "project.project",
        string="Related Project",
        index=True,
        help="Project this RFQ is for",
    )
    
    # Service being requested
    service_type = fields.Selection(
        selection=SERVICE_TYPES,
        string="Service Type",
        required=True,
        tracking=True,
    )
    service_description = fields.Text(
        string="Service Description",
        help="Detailed description of what's needed",
    )
    
    # Event details
    event_name = fields.Char(
        string="Event Name",
        compute="_compute_event_details",
        store=True,
    )
    event_date = fields.Date(
        string="Event Date",
        compute="_compute_event_details",
        store=True,
    )
    event_venue = fields.Char(
        string="Event Venue",
        compute="_compute_event_details",
        store=True,
    )
    guest_count = fields.Integer(
        string="Guest Count",
        compute="_compute_event_details",
        store=True,
    )
    
    # Quote details
    estimated_budget = fields.Monetary(
        string="Estimated Budget",
        currency_field="currency_id",
        help="Our estimated budget for this service",
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        required=True,
        default=lambda self: self.env.company.currency_id,
    )
    
    # Timing
    quote_date = fields.Date(
        string="RFQ Date",
        default=fields.Date.today,
    )
    closing_date = fields.Date(
        string="Closing Date",
        required=True,
        default=lambda self: self._get_default_closing_date(),
        help="Deadline for vendors to submit quotes",
    )
    service_date = fields.Date(
        string="Service Date",
        help="When the service is needed",
    )
    
    @api.model
    def _get_default_closing_date(self):
        """Return default closing date (7 days from today)."""
        return fields.Date.add(fields.Date.today(), days=7)
    
    # Vendors
    vendor_ids = fields.Many2many(
        "res.partner",
        string="Invited Vendors",
        domain="[('ptt_is_vendor', '=', True)]",
        help="Vendors invited to quote",
    )
    quote_history_ids = fields.One2many(
        "ptt.vendor.quote.history",
        "rfq_id",
        string="Vendor Quotes",
    )
    quote_count = fields.Integer(
        string="Quote Count",
        compute="_compute_quote_count",
    )
    
    # Approval
    approved_vendor_id = fields.Many2one(
        "res.partner",
        string="Approved Vendor",
        tracking=True,
    )
    approved_quote_id = fields.Many2one(
        "ptt.vendor.quote.history",
        string="Approved Quote",
    )
    approved_price = fields.Monetary(
        string="Approved Price",
        currency_field="currency_id",
        related="approved_quote_id.quoted_price",
    )
    
    # Assignment created from this RFQ
    vendor_assignment_id = fields.Many2one(
        "ptt.project.vendor.assignment",
        string="Created Assignment",
    )
    
    # Responsibility
    user_id = fields.Many2one(
        "res.users",
        string="Responsible",
        default=lambda self: self.env.user,
        tracking=True,
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
    )
    
    # Status
    state = fields.Selection([
        ("draft", "Draft"),
        ("pending", "Pending Approval"),
        ("sent", "Sent to Vendors"),
        ("in_progress", "Quotes Received"),
        ("done", "Vendor Selected"),
        ("assigned", "Assignment Created"),
        ("cancel", "Cancelled"),
    ], string="Status", default="draft", tracking=True)
    
    # Notes
    notes = fields.Html(string="Notes")

    @api.depends(
        "crm_lead_id", "crm_lead_id.ptt_event_name", "crm_lead_id.ptt_event_date",
        "crm_lead_id.ptt_venue_name", "crm_lead_id.ptt_guest_count",
        "project_id", "project_id.ptt_event_name", "project_id.ptt_event_date",
        "project_id.ptt_venue_name", "project_id.ptt_guest_count"
    )
    def _compute_event_details(self):
        """Pull event details from linked lead or project."""
        for rfq in self:
            if rfq.project_id:
                rfq.event_name = rfq.project_id.ptt_event_name
                rfq.event_date = rfq.project_id.ptt_event_date
                rfq.event_venue = rfq.project_id.ptt_venue_name
                rfq.guest_count = rfq.project_id.ptt_guest_count
            elif rfq.crm_lead_id:
                rfq.event_name = rfq.crm_lead_id.ptt_event_name
                rfq.event_date = rfq.crm_lead_id.ptt_event_date
                rfq.event_venue = rfq.crm_lead_id.ptt_venue_name
                rfq.guest_count = rfq.crm_lead_id.ptt_guest_count
            else:
                rfq.event_name = False
                rfq.event_date = False
                rfq.event_venue = False
                rfq.guest_count = 0

    @api.depends("quote_history_ids")
    def _compute_quote_count(self):
        """Compute count of vendor quote submissions for this RFQ."""
        for rfq in self:
            rfq.quote_count = len(rfq.quote_history_ids)

    @api.model_create_multi
    def create(self, vals_list):
        """Generate sequence on create."""
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "ptt.vendor.rfq"
                ) or _("New")
        return super().create(vals_list)

    def action_send_to_vendors(self):
        """Send RFQ to all invited vendors via email."""
        self.ensure_one()
        if not self.vendor_ids:
            raise UserError(_("Please add at least one vendor to send the RFQ."))
        
        template = self.env.ref(
            "ptt_vendor_management.email_template_vendor_rfq",
            raise_if_not_found=False,
        )
        
        if template:
            for vendor in self.vendor_ids:
                template.with_context(
                    vendor_name=vendor.name,
                    lang=vendor.lang,
                ).send_mail(self.id, email_values={
                    "email_to": vendor.email,
                    "email_from": self.env.user.partner_id.email,
                }, force_send=True)
        
        self.state = "sent"
        self.message_post(
            body=_("RFQ sent to %d vendors: %s") % (
                len(self.vendor_ids),
                ", ".join(self.vendor_ids.mapped("name"))
            ),
            message_type="notification",
        )

    def action_pending(self):
        """Mark as pending approval."""
        self.state = "pending"

    def action_cancel(self):
        """Cancel the RFQ."""
        self.state = "cancel"

    def action_reset_to_draft(self):
        """Reset to draft."""
        self.state = "draft"

    def action_select_vendor(self):
        """Open wizard to select winning vendor."""
        self.ensure_one()
        if not self.quote_history_ids:
            raise UserError(_("No quotes received yet."))
        
        return {
            "type": "ir.actions.act_window",
            "name": _("Select Vendor"),
            "res_model": "ptt.rfq.select.vendor",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_rfq_id": self.id,
                "default_quote_ids": self.quote_history_ids.ids,
            },
        }

    def action_approve_vendor(self, vendor_id, quote_id=None):
        """Approve a vendor for this RFQ."""
        self.ensure_one()
        quote = None
        if quote_id:
            quote = self.env["ptt.vendor.quote.history"].browse(quote_id)
        else:
            quote = self.quote_history_ids.filtered(
                lambda q: q.vendor_id.id == vendor_id
            )[:1]
        
        self.write({
            "approved_vendor_id": vendor_id,
            "approved_quote_id": quote.id if quote else False,
            "state": "done",
        })
        
        self.message_post(
            body=_("Vendor %s approved for this RFQ") % self.approved_vendor_id.name,
            message_type="notification",
        )

    def action_create_assignment(self):
        """Create a vendor assignment from approved RFQ."""
        self.ensure_one()
        if not self.approved_vendor_id:
            raise UserError(_("Please approve a vendor first."))
        if not self.project_id:
            raise UserError(_("Please link a project to create an assignment."))
        
        assignment = self.env["ptt.project.vendor.assignment"].create({
            "project_id": self.project_id.id,
            "service_type": self.service_type,
            "vendor_id": self.approved_vendor_id.id,
            "estimated_cost": self.approved_price or self.estimated_budget,
            "service_date": self.service_date,
            "description": self.service_description,
            "status": "confirmed",
        })
        
        self.write({
            "vendor_assignment_id": assignment.id,
            "state": "assigned",
        })
        
        return {
            "type": "ir.actions.act_window",
            "name": _("Vendor Assignment"),
            "res_model": "ptt.project.vendor.assignment",
            "res_id": assignment.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_view_quotes(self):
        """View all quotes for this RFQ."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Vendor Quotes"),
            "res_model": "ptt.vendor.quote.history",
            "view_mode": "list,form",
            "domain": [("rfq_id", "=", self.id)],
            "context": {"default_rfq_id": self.id},
        }


class PttVendorQuoteHistory(models.Model):
    """Vendor quote submissions for RFQs."""
    _name = "ptt.vendor.quote.history"
    _description = "Vendor Quote History"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "quoted_price asc"
    _rec_name = "vendor_id"

    rfq_id = fields.Many2one(
        "ptt.vendor.rfq",
        string="RFQ",
        required=True,
        ondelete="cascade",
    )
    vendor_id = fields.Many2one(
        "res.partner",
        string="Vendor",
        required=True,
        domain="[('ptt_is_vendor', '=', True)]",
    )
    
    # Quote details
    quoted_price = fields.Monetary(
        string="Quoted Price",
        currency_field="currency_id",
        required=True,
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        related="rfq_id.currency_id",
    )
    
    # Timing
    quote_date = fields.Datetime(
        string="Quote Submitted",
        default=fields.Datetime.now,
    )
    estimated_delivery_date = fields.Date(
        string="Estimated Availability",
        help="When vendor can provide the service",
    )
    
    # Details
    notes = fields.Text(string="Vendor Notes")
    
    # Status
    is_approved = fields.Boolean(
        string="Approved",
        compute="_compute_is_approved",
        store=True,
        tracking=True,
    )

    @api.depends("rfq_id.approved_quote_id")
    def _compute_is_approved(self):
        """Check if this quote is the approved one for its RFQ."""
        for quote in self:
            quote.is_approved = quote.id == quote.rfq_id.approved_quote_id.id

    @api.constrains('rfq_id', 'vendor_id')
    def _check_rfq_open_for_quotes(self):
        """Ensure quotes can only be submitted to open RFQs."""
        for quote in self:
            if quote.rfq_id.state in ('done', 'assigned', 'cancel'):
                raise UserError(_(
                    "Cannot submit quotes to RFQ '%s' - it is already %s.",
                    quote.rfq_id.name,
                    quote.rfq_id.state,
                ))

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to validate RFQ state before quote submission."""
        for vals in vals_list:
            if 'rfq_id' in vals:
                rfq = self.env['ptt.vendor.rfq'].browse(vals['rfq_id'])
                if rfq.state in ('done', 'assigned', 'cancel'):
                    raise UserError(_(
                        "Cannot submit quotes to RFQ '%s' - it is already %s.",
                        rfq.name,
                        rfq.state,
                    ))
        return super().create(vals_list)

    def action_approve(self):
        """Approve this quote and its vendor for the RFQ.
        
        Delegates to the parent RFQ's action_approve_vendor method.
        """
        self.ensure_one()
        self.rfq_id.action_approve_vendor(self.vendor_id.id, self.id)
