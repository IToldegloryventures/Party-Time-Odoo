# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

from odoo.addons.ptt_business_core.constants import (
    CONTACT_METHODS,
    LEAD_TYPES,
    LOCATION_TYPES,
    PAYMENT_STATUS,
    TIME_SELECTIONS,
)


class CrmLead(models.Model):
    """CRM Lead extensions for Party Time Texas event management."""
    _inherit = "crm.lead"

    # =========================================================================
    # SQL CONSTRAINTS
    # =========================================================================
    _sql_constraints = [
        ('positive_ptt_guest_count', 'CHECK (ptt_guest_count >= 0)',
         'Guest count cannot be negative.'),
        ('positive_ptt_event_duration', 'CHECK (ptt_event_duration >= 0)',
         'Event duration cannot be negative.'),
    ]

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
        help="Client's preferred contact method. Syncs with Contact card when linked.",
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
    # NOTE: Event type (ptt_event_type) is a REQUIRED Selection field defined 
    # in ptt_enhanced_sales module. Values: corporate, social, wedding.
    # Sale Order and Project get this value via related fields.
    ptt_event_name = fields.Char(
        string="Event Name",
        help="Name/title of the event (e.g., 'Smith Wedding Reception')",
    )
    ptt_event_date = fields.Date(
        string="Event Date",
        help="Date of the event",
    )
    ptt_event_goal = fields.Char(string="Event Goal")
    ptt_event_time = fields.Char(
        string="Event Time",
        help="Approximate event start time (e.g., '6:00 PM'). Used for initial planning."
    )
    ptt_setup_time = fields.Selection(
        selection=TIME_SELECTIONS,
        string="Setup Time",
        help="Time when setup begins",
    )
    ptt_start_time = fields.Selection(
        selection=TIME_SELECTIONS,
        string="Start Time",
        help="Event start time",
    )
    ptt_end_time = fields.Selection(
        selection=TIME_SELECTIONS,
        string="End Time",
        help="Event end time",
    )
    ptt_teardown_time = fields.Selection(
        selection=TIME_SELECTIONS,
        string="Teardown Time",
        help="Time when teardown/breakdown should be complete",
    )
    ptt_event_duration = fields.Float(
        string="Duration (Hours)",
        help="Estimated event duration. Maps to ptt_total_hours on project."
    )
    ptt_guest_count = fields.Integer(string="Guest Count")
    ptt_attire = fields.Selection(
        selection=[
            ('casual', 'Casual'),
            ('business_casual', 'Business Casual'),
            ('formal', 'Formal'),
            ('themed', 'Themed'),
        ],
        string="Attire",
        help="Dress code for the event",
    )
    
    # Venue Information
    ptt_venue_name = fields.Char(
        string="Venue Name",
        help="Name of the event venue",
    )
    ptt_venue_address = fields.Text(
        string="Address",
        help="Full address of the venue",
    )
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
    # NATIVE ODOO EXTENSION - Copy custom fields to Contact on conversion
    # =========================================================================
    def _prepare_customer_values(self, partner_name, is_company=False, parent_id=False):
        """Extend native method to copy ptt_preferred_contact to new Contact.
        
        This is called by Odoo when converting a lead to opportunity and
        creating a new contact. We add our custom field to the values.
        """
        res = super()._prepare_customer_values(partner_name, is_company=is_company, parent_id=parent_id)
        # Add our custom field to be copied to the new Contact
        if self.ptt_preferred_contact:
            res['ptt_preferred_contact'] = self.ptt_preferred_contact
        return res

    def _ptt_find_matching_partner(self):
        """Extended partner matching - searches by email, phone, or company name.
        
        Extends Odoo's native _find_matching_partner() to check multiple fields:
        1. Email (normalized)
        2. Phone (sanitized)
        3. Company/Partner name
        
        Returns first match found, prioritizing email > phone > name.
        """
        self.ensure_one()
        Partner = self.env['res.partner']
        
        # Already has partner
        if self.partner_id:
            return self.partner_id
        
        # 1. Try email match first (most reliable)
        if self.email_from:
            partner = self._find_matching_partner()  # Use Odoo's native email search
            if partner:
                return partner
        
        # 2. Try phone match
        if self.phone:
            # Use sanitized phone for better matching
            phone_sanitized = self.phone_sanitized
            if phone_sanitized:
                partner = Partner.search([
                    '|',
                    ('phone_sanitized', '=', phone_sanitized),
                    ('mobile', 'ilike', self.phone[-7:]),  # Last 7 digits
                ], limit=1)
                if partner:
                    return partner
        
        # 3. Try company name match (exact)
        if self.partner_name:
            partner = Partner.search([
                ('is_company', '=', True),
                ('name', '=ilike', self.partner_name),
            ], limit=1)
            if partner:
                return partner
        
        # 4. Try contact name match (less reliable, only if email domain matches)
        if self.contact_name and self.email_from:
            email_domain = self.email_from.split('@')[-1] if '@' in self.email_from else False
            if email_domain and email_domain not in ('gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com'):
                partner = Partner.search([
                    ('name', '=ilike', self.contact_name),
                    ('email', 'ilike', f'@{email_domain}'),
                ], limit=1)
                if partner:
                    return partner
        
        return Partner  # Empty recordset

    @api.onchange('email_from', 'phone', 'partner_name', 'contact_name')
    def _onchange_find_matching_partner(self):
        """Auto-link existing contact when key fields are entered.
        
        Searches by: email, phone, company name, contact name.
        """
        if not self.partner_id:
            matching_partner = self._ptt_find_matching_partner()
            if matching_partner:
                self.partner_id = matching_partner

    @api.onchange('partner_id')
    def _onchange_partner_preferred_contact(self):
        """When partner is linked (manually or auto), pull their preferred contact."""
        if self.partner_id and self.partner_id.ptt_preferred_contact and not self.ptt_preferred_contact:
            self.ptt_preferred_contact = self.partner_id.ptt_preferred_contact

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

    # NOTE: Projects are created automatically when a Sale Order with 
    # "Event Kickoff" product is confirmed. See sale_order.py for logic.
