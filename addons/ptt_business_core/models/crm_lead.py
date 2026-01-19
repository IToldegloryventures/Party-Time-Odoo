# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

from odoo.addons.ptt_business_core.constants import (
    CONTACT_METHODS,
    LEAD_TYPES,
    LOCATION_TYPES,
    PAYMENT_STATUS,
)


class CrmLead(models.Model):
    """CRM Lead extensions for Party Time Texas event management."""
    _inherit = "crm.lead"

    _positive_ptt_guest_count = models.Constraint(
        "CHECK (ptt_guest_count >= 0)",
        "Guest count cannot be negative.",
    )
    _positive_ptt_event_duration = models.Constraint(
        "CHECK (ptt_event_duration >= 0)",
        "Event duration cannot be negative.",
    )

    # =========================================================================
    # CONTACT INFORMATION
    # =========================================================================
    ptt_date_of_call = fields.Date(
        string="Date of Call",
        help="Date of the initial inquiry call.",
    )
    ptt_preferred_contact = fields.Selection(
        selection=CONTACT_METHODS,
        string="Preferred Contact Method",
    )
    ptt_lead_type = fields.Selection(
        selection=LEAD_TYPES,
        string="Lead Type",
        help="Whether this lead is an individual or business client.",
    )
    
    # Secondary Point of Contact
    ptt_secondary_contact_name = fields.Char(string="2nd Contact Name")
    ptt_secondary_contact_phone = fields.Char(string="2nd Contact Phone")
    ptt_secondary_contact_email = fields.Char(string="2nd Contact Email")

    # =========================================================================
    # EVENT IDENTITY
    # =========================================================================
    ptt_event_id = fields.Char(
        string="Event ID",
        readonly=True,
        copy=False,
        index=True,
        help="Unique event identifier (e.g., EVT-2026-0001). Generated when the sale order is confirmed. Used to track event across CRM, Sales, Projects, and Tasks.",
    )

    # =========================================================================
    # EVENT OVERVIEW
    # =========================================================================
    # NOTE: Event type is now managed via ptt_event_type_id (Many2one to sale.order.type)
    # which links to one of 3 types: Corporate, Social, Wedding
    # The deprecated ptt_event_type selection field has been removed.
    
    # Studio fields (x_studio_event_name, x_studio_event_date, x_studio_venue_name,
    # x_studio_venue_address) already exist in DB from Odoo Studio - no need to redeclare.
    # Use them directly in views and code.
    
    ptt_event_goal = fields.Char(string="Event Goal")
    ptt_event_time = fields.Char(
        string="Event Time",
        help="Approximate event start time (e.g., '6:00 PM'). Used for initial planning."
    )
    ptt_event_duration = fields.Float(
        string="Duration (Hours)",
        help="Estimated event duration. Maps to ptt_total_hours on project."
    )
    ptt_guest_count = fields.Integer(string="Estimated Guest Count")
    
    # Venue Information
    ptt_venue_booked = fields.Boolean(string="Venue Booked?")
    ptt_location_type = fields.Selection(
        selection=LOCATION_TYPES,
        string="Location Type",
    )

    # =========================================================================
    # SERVICE DETAILS (Optional - Captured When Relevant)
    # =========================================================================
    # DJ Details
    ptt_dj_music_styles = fields.Text(string="Desired Music Styles")
    ptt_dj_mc_needed = fields.Boolean(string="MC Services Needed?")
    ptt_dj_karaoke = fields.Boolean(string="Karaoke Desired?")
    
    # Photo Booth Details
    ptt_photobooth_type = fields.Selection(
        [
            ("360", "360 Booth"),
            ("standard", "Standard Booth"),
            ("ai", "AI Booth"),
            ("green_screen", "Green Screen"),
        ],
        string="Photo Booth Type",
    )
    ptt_photobooth_branding = fields.Boolean(string="Custom Branding?")
    
    # Casino Details
    ptt_casino_games = fields.Text(string="Desired Games")
    ptt_casino_player_count = fields.Integer(string="Expected Players")
    
    # General Service Notes
    ptt_service_notes = fields.Text(
        string="Service Notes",
        help="Additional notes about the client's service needs, special requests, or important details."
    )

    # =========================================================================
    # BUDGET & FINANCIAL
    # =========================================================================
    ptt_budget_range = fields.Char(string="Budget Range")
    ptt_services_already_booked = fields.Text(string="Services Already Booked")
    
    # Finance Contact
    ptt_finance_contact_name = fields.Char(string="Finance Contact Name")
    ptt_finance_contact_phone = fields.Char(string="Finance Contact Phone")
    ptt_finance_contact_email = fields.Char(string="Finance Contact Email")

    # =========================================================================
    # SERVICE LINES (Structured service selection before quote)
    # =========================================================================
    ptt_service_line_ids = fields.One2many(
        "ptt.crm.service.line",
        "crm_lead_id",
        string="Service Lines",
        help="Structured breakdown of proposed services with tiers and pricing",
    )
    ptt_service_lines_total = fields.Monetary(
        string="Services Total",
        compute="_compute_service_lines_total",
        store=True,
        currency_field="company_currency",
        help="Total of all proposed service lines",
    )

    # =========================================================================
    # VENDOR COST ESTIMATES (One2many to estimate model)
    # =========================================================================
    ptt_vendor_estimate_ids = fields.One2many(
        "ptt.crm.vendor.estimate",
        "crm_lead_id",
        string="Vendor Cost Estimates",
    )
    ptt_estimated_vendor_total = fields.Monetary(
        string="Total Estimated Vendor Costs",
        compute="_compute_financials",
        store=True,
        currency_field="company_currency",
    )
    ptt_estimated_client_total = fields.Monetary(
        string="Estimated Client Total",
        currency_field="company_currency",
    )
    ptt_estimated_margin = fields.Monetary(
        string="Estimated Margin",
        compute="_compute_financials",
        store=True,
        currency_field="company_currency",
    )
    ptt_margin_percent = fields.Float(
        string="Margin %",
        compute="_compute_financials",
        store=True,
    )

    # =========================================================================
    # PROJECT INTEGRATION
    # =========================================================================
    ptt_project_id = fields.Many2one(
        "project.project",
        string="Related Project",
        readonly=True,
    )
    ptt_project_count = fields.Integer(
        string="Project Count",
        compute="_compute_project_count",
    )
    
    # =========================================================================
    # SALE ORDER INTEGRATION
    # =========================================================================
    ptt_sale_order_count = fields.Integer(
        string="Sale Order Count",
        compute="_compute_sale_order_count",
    )

    # =========================================================================
    # INVOICE TRACKING
    # =========================================================================
    ptt_invoice_count = fields.Integer(
        string="Invoice Count",
        compute="_compute_invoice_data",
    )
    ptt_invoice_total = fields.Monetary(
        string="Invoice Total",
        compute="_compute_invoice_data",
        currency_field="company_currency",
    )
    ptt_invoice_paid = fields.Monetary(
        string="Amount Paid",
        compute="_compute_invoice_data",
        currency_field="company_currency",
    )
    ptt_invoice_remaining = fields.Monetary(
        string="Amount Remaining",
        compute="_compute_invoice_data",
        currency_field="company_currency",
    )
    ptt_payment_status = fields.Selection(
        selection=PAYMENT_STATUS,
        string="Payment Status",
        compute="_compute_invoice_data",
    )

    # =========================================================================
    # FOLLOW-UP & STAGE TRACKING
    # =========================================================================
    ptt_followup_email_sent = fields.Boolean(string="Follow-up Email Sent")
    ptt_proposal_sent = fields.Boolean(
        string="Proposal Sent",
        help="Automatically set to True when quotation is sent to customer.",
    )
    ptt_contract_sent = fields.Boolean(
        string="Contract Sent",
        help="Set to True when formal contract is sent for customer signature.",
    )
    ptt_booked = fields.Boolean(
        string="Event Booked",
        help="Set to True when customer confirms and deposit is received.",
    )
    ptt_next_contact_date = fields.Date(string="Next Contact Date")

    # =========================================================================
    # COMPUTED METHODS
    # =========================================================================
    @api.depends("ptt_service_line_ids.subtotal")
    def _compute_service_lines_total(self):
        """Compute total of all proposed service lines."""
        for lead in self:
            lead.ptt_service_lines_total = sum(lead.ptt_service_line_ids.mapped("subtotal"))

    @api.depends("ptt_vendor_estimate_ids.estimated_cost", "ptt_estimated_client_total")
    def _compute_financials(self):
        """Compute estimated vendor total, margin, and margin percentage.
        
        Calculates:
        - ptt_estimated_vendor_total: Sum of all vendor estimate costs
        - ptt_estimated_margin: Client total minus vendor costs
        - ptt_margin_percent: Margin as percentage of client total
        """
        for lead in self:
            vendor_total = sum(lead.ptt_vendor_estimate_ids.mapped("estimated_cost"))
            lead.ptt_estimated_vendor_total = vendor_total
            lead.ptt_estimated_margin = (lead.ptt_estimated_client_total or 0) - vendor_total
            if lead.ptt_estimated_client_total:
                lead.ptt_margin_percent = (lead.ptt_estimated_margin / lead.ptt_estimated_client_total) * 100
            else:
                lead.ptt_margin_percent = 0.0

    @api.depends("ptt_project_id")
    def _compute_project_count(self):
        """Compute project count for smart button display.
        
        Returns 1 if a project is linked, 0 otherwise.
        """
        for lead in self:
            lead.ptt_project_count = 1 if lead.ptt_project_id else 0

    @api.depends("order_ids")
    def _compute_sale_order_count(self):
        """Compute count of sale orders linked to this lead.
        
        Uses the standard order_ids relation from crm module.
        """
        for lead in self:
            lead.ptt_sale_order_count = len(lead.order_ids)

    @api.depends("order_ids.invoice_ids")
    def _compute_invoice_data(self):
        """Compute invoice statistics and payment status.
        
        Calculates:
        - ptt_invoice_count: Number of customer invoices
        - ptt_invoice_total: Sum of invoice totals
        - ptt_invoice_paid: Amount already paid
        - ptt_invoice_remaining: Outstanding balance
        - ptt_payment_status: paid/partial/overdue/not_paid
        """
        for lead in self:
            invoices = lead.order_ids.mapped("invoice_ids").filtered(
                lambda inv: inv.move_type == "out_invoice"
            )
            lead.ptt_invoice_count = len(invoices)
            lead.ptt_invoice_total = sum(invoices.mapped("amount_total"))
            lead.ptt_invoice_paid = lead.ptt_invoice_total - sum(invoices.mapped("amount_residual"))
            lead.ptt_invoice_remaining = sum(invoices.mapped("amount_residual"))
            
            # Determine payment status
            if not invoices or lead.ptt_invoice_total == 0:
                lead.ptt_payment_status = "not_paid"
            elif lead.ptt_invoice_remaining == 0:
                lead.ptt_payment_status = "paid"
            elif lead.ptt_invoice_paid > 0:
                lead.ptt_payment_status = "partial"
            else:
                overdue = invoices.filtered(
                    lambda inv: inv.invoice_date_due 
                    and inv.invoice_date_due < fields.Date.today() 
                    and inv.amount_residual > 0
                )
                lead.ptt_payment_status = "overdue" if overdue else "not_paid"

    # =========================================================================
    # ACTION METHODS
    # =========================================================================
    def action_view_project(self):
        """View linked project."""
        self.ensure_one()
        if not self.ptt_project_id:
            return
        return {
            "type": "ir.actions.act_window",
            "name": "Project",
            "res_model": "project.project",
            "res_id": self.ptt_project_id.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_view_invoices(self):
        """View linked invoices."""
        self.ensure_one()
        invoices = self.order_ids.mapped("invoice_ids")
        return {
            "type": "ir.actions.act_window",
            "name": "Invoices",
            "res_model": "account.move",
            "view_mode": "list,form",
            "domain": [("id", "in", invoices.ids)],
            "target": "current",
        }

    def action_view_sale_orders(self):
        """View linked sale orders (confirmed quotes)."""
        self.ensure_one()
        orders = self.order_ids
        if len(orders) == 1:
            return {
                "type": "ir.actions.act_window",
                "name": "Sale Order",
                "res_model": "sale.order",
                "res_id": orders.id,
                "view_mode": "form",
                "target": "current",
            }
        return {
            "type": "ir.actions.act_window",
            "name": "Sale Orders",
            "res_model": "sale.order",
            "view_mode": "list,form",
            "domain": [("id", "in", orders.ids)],
            "target": "current",
        }

    def _ensure_event_id(self):
        """Ensure the event ID exists, generating it when missing."""
        self.ensure_one()
        if not self.ptt_event_id:
            event_id = self.env["ir.sequence"].next_by_code("ptt.event.id")
            if not event_id:
                raise UserError(_("Missing sequence for Event ID (code: ptt.event.id)."))
            self.ptt_event_id = event_id
        return self.ptt_event_id

    def action_generate_event_id(self):
        """Generate event ID for this opportunity if not already set."""
        self._ensure_event_id()
        return {"type": "ir.actions.client", "tag": "reload"}

    def action_create_project(self):
        """Create project from this opportunity."""
        self.ensure_one()
        if self.ptt_project_id:
            raise UserError(_("A project already exists for this opportunity."))
        if not self.partner_id:
            raise UserError(_("Please set a customer before creating a project."))

        # Ensure event ID exists (generate if needed)
        event_id = self._ensure_event_id()

        project_vals = {
            "name": f"Event {event_id} - {self.partner_id.name} - {self.x_studio_event_name or self.name}",
            "partner_id": self.partner_id.id,
            "user_id": self.user_id.id,
            "ptt_crm_lead_id": self.id,
            "ptt_event_id": event_id,
            # NOTE: ptt_event_type removed - use ptt_event_type_id (Many2one) instead
            # Use Studio fields directly - no aliases
            "x_studio_event_name": self.x_studio_event_name,
            "x_studio_event_date": self.x_studio_event_date,
            "ptt_guest_count": self.ptt_guest_count,
            "x_studio_venue_name": self.x_studio_venue_name,
            "ptt_total_hours": self.ptt_event_duration,  # Map legacy field to new field
        }

        project = self.env["project.project"].create(project_vals)
        self.ptt_project_id = project.id

        # Copy vendor estimates to project assignments
        for estimate in self.ptt_vendor_estimate_ids:
            self.env["ptt.project.vendor.assignment"].create({
                "project_id": project.id,
                "service_type": estimate.service_type,
                "estimated_cost": estimate.estimated_cost,
                "notes": f"Transferred from CRM: {estimate.vendor_name or ''}",
            })

        return {
            "type": "ir.actions.act_window",
            "name": "Project Created",
            "res_model": "project.project",
            "res_id": project.id,
            "view_mode": "form",
            "target": "current",
        }

