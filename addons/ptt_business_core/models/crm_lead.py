from odoo import models, fields, api, _
from odoo.exceptions import UserError


class CrmLead(models.Model):
    _inherit = "crm.lead"

    # === TIER 1: LEAD CONTACT INFORMATION ===
    # NOTE: user_id = Sales Rep (standard Odoo field - use that, not x_sales_rep_id)
    # NOTE: contact_name = First/Last Name (standard Odoo field)
    # NOTE: partner_name = Company Name (standard Odoo field)
    # NOTE: phone = Phone Number (standard Odoo field)
    # NOTE: email_from = Email Address (standard Odoo field)
    # NOTE: description = Additional Notes (standard Odoo field - use that)
    
    x_date_of_call = fields.Date(
        string="Date of Call",
        help="Date of the initial inquiry call.",
    )
    x_preferred_contact_method = fields.Selection(
        [
            ("call", "Phone Call"),
            ("text", "Text Message"),
            ("email", "Email"),
        ],
        string="Preferred Contact Method",
    )
    x_second_poc_name = fields.Char(string="2nd POC Name")
    x_second_poc_phone = fields.Char(string="2nd POC Phone")
    x_second_poc_email = fields.Char(string="2nd POC Email")

    x_lead_type = fields.Selection(
        [
            ("individual", "Individual"),
            ("business", "Business"),
        ],
        string="Lead Type",
        help="Whether this lead is an individual or a business client.",
    )

    # === EVENT ID (Manual Entry - Links CRM, SO, Project, Tasks) ===
    x_event_id = fields.Char(
        string="Event ID",
        copy=False,
        index=True,
        tracking=True,
        help="Unique event identifier. Enter manually to link this opportunity with its Project and Tasks.",
    )

    x_inquiry_source = fields.Selection(
        [
            ("web_form", "Web Form"),
            ("phone", "Phone Call"),
            ("email", "Email"),
            ("referral", "Referral"),
            ("walk_in", "Walk-In"),
            ("social_media", "Social Media"),
        ],
        string="Lead Source",
        default="phone",
        tracking=True,
        help="How did this lead find us?",
    )

    x_referral_source = fields.Char(
        string="Referral Details",
        help="If referral, who referred this client?",
    )

    # === TIER 1: EVENT OVERVIEW ===
    x_event_type = fields.Selection(
        [
            # Corporate Events
            ("corporate_conference", "Corporate - Conferences & Conventions"),
            ("corporate_groundbreaking", "Corporate - Groundbreaking Ceremonies"),
            ("corporate_ribbon_cutting", "Corporate - Ribbon Cuttings"),
            ("corporate_product_launch", "Corporate - Product Launches"),
            ("corporate_awards", "Corporate - Awards Banquets"),
            ("corporate_team_building", "Corporate - Team Building Experiences"),
            ("corporate_holiday", "Corporate - Holiday Parties & Picnics"),
            # Community Events
            ("community_hoa", "Community - HOA's & Country Clubs"),
            ("community_cities_schools", "Community - Cities & Schools"),
            ("community_festivals", "Community - Seasonal Festivals"),
            ("community_pool_party", "Community - Pool Parties & Picnics"),
            ("community_holiday", "Community - Holiday Themed"),
            ("community_movie_night", "Community - Outdoor Movie Nights"),
            ("community_vendor_fair", "Community - Vendor & Artisan Fairs"),
            # Charities & Fundraisers
            ("charity_banquet", "Charities - Banquets & Galas"),
            ("charity_race", "Charities - Races (5k, Fun-run, etc.)"),
            ("charity_awareness", "Charities - Awareness Campaigns"),
            ("charity_donor", "Charities - Donor Recognition"),
            # Private Celebrations
            ("private_luxury", "Private - Luxury Private Parties"),
            ("private_wedding", "Private - Weddings"),
            ("private_graduation", "Private - Graduations"),
            ("private_reunion", "Private - Reunions"),
            ("private_cultural", "Private - Cultural Experiences"),
            ("private_barmitzvah", "Private - Bar/Bat Mitzvahs"),
            ("private_desi", "Private - Desi Celebrations"),
            ("private_quinceanera", "Private - Quinceañeras"),
            ("private_birthday", "Private - Birthday Parties"),
            # Themed Events
            ("themed_casino", "Themed - Casino Nights"),
            ("themed_watch_party", "Themed - Watch Parties"),
            ("themed_sports", "Themed - Sports Parties"),
            ("themed_decade", "Themed - Decade-Themed Events"),
            ("themed_masquerade", "Themed - Masquerade Balls"),
            ("themed_cigar_whiskey", "Themed - Cigar & Whiskey Nights"),
        ],
        string="Event Category",
    )
    x_event_name = fields.Char(string="Event Name (if known)")
    x_event_specific_goal = fields.Char(string="Specific Goal")
    x_event_date = fields.Date(string="Scheduled Date", index=True)
    x_event_time = fields.Char(string="Event Time")
    x_total_hours = fields.Float(string="Total Hours")
    x_estimated_guest_count = fields.Integer(string="Estimated Guest Count")
    x_venue_booked = fields.Boolean(string="Event Venue (if booked)")
    x_venue_name = fields.Char(string="Venue")
    x_event_location_type = fields.Selection(
        [
            ("indoor", "Indoor"),
            ("outdoor", "Outdoor"),
            ("combination", "Combination"),
        ],
        string="Event Location",
    )

    # === TIER 2: SERVICES REQUESTED (CHECKBOXES ONLY) ===
    x_service_dj = fields.Boolean(string="DJ/MC Services")
    x_service_photovideo = fields.Boolean(string="Photo/Video")
    x_service_live_entertainment = fields.Boolean(string="Live Entertainment")
    x_service_lighting = fields.Boolean(string="Lighting/AV")
    x_service_decor = fields.Boolean(string="Decor/Thematic Design")
    x_service_venue_sourcing = fields.Boolean(string="Venue Sourcing")
    x_service_catering = fields.Boolean(string="Catering")
    x_service_transportation = fields.Boolean(string="Transportation")
    x_service_rentals = fields.Boolean(string="Rentals (General)")
    x_service_photobooth = fields.Boolean(string="Photo Booth Rentals")
    x_service_caricature = fields.Boolean(string="Caricature Artists")
    x_service_casino = fields.Boolean(string="Casino Services")
    x_service_staffing = fields.Boolean(
        string="Staffing (hosts, bartenders, security)"
    )

    # === FOLLOW-UP INFORMATION ===
    x_followup_email_sent = fields.Boolean(string="Follow-up Email Sent?")
    x_proposal_sent = fields.Boolean(string="Proposal Sent?")
    x_next_contact_date = fields.Date(string="Next Scheduled Contact Date")

    # === BUDGET & FINANCIAL ===
    x_budget_range = fields.Char(string="Total Event Budget (range)")
    x_services_already_booked = fields.Text(string="Services Already Booked (if any)")
    x_cfo_name = fields.Char(string="CFO/Finance Contact Name")
    x_cfo_phone = fields.Char(string="CFO/Finance Contact Phone")
    x_cfo_email = fields.Char(string="CFO/Finance Contact Email")
    x_cfo_contact_method = fields.Selection(
        [
            ("call", "Phone Call"),
            ("text", "Text Message"),
            ("email", "Email"),
        ],
        string="CFO Preferred Contact Method",
    )

    # === PROJECT LINK ===
    x_project_id = fields.Many2one(
        "project.project",
        string="Related Project",
        help="Project created from this opportunity.",
        index=True,
        ondelete="set null",
    )
    project_count = fields.Integer(
        string="# Projects",
        compute="_compute_project_count",
        help="Counter for the project linked to this lead",
    )
    
    x_has_project = fields.Boolean(
        string="Has Project",
        compute="_compute_project_count",
        help="True if this lead has a linked project (via x_project_id or confirmed Sales Order)",
    )

    @api.depends("x_project_id", "order_ids", "order_ids.state", "order_ids.project_ids")
    def _compute_project_count(self):
        for record in self:
            if record.x_project_id:
                record.project_count = 1
                record.x_has_project = True
            else:
                confirmed_orders = record.order_ids.filtered(lambda so: so.state == 'sale')
                if confirmed_orders:
                    projects_from_so = confirmed_orders.mapped('project_ids').filtered(lambda p: p)
                    projects_from_crm = self.env['project.project'].search([
                        ('x_crm_lead_id', '=', record.id)
                    ])
                    all_projects = (projects_from_so | projects_from_crm)
                    if all_projects:
                        record.project_count = len(all_projects)
                        record.x_has_project = True
                    else:
                        record.project_count = 0
                        record.x_has_project = False
                else:
                    record.project_count = 0
                    record.x_has_project = False

    x_project_task_count = fields.Integer(
        string="# Project Tasks",
        compute="_compute_project_task_count",
        help="Number of tasks in the related project",
    )

    @api.depends("x_project_id", "x_project_id.task_count")
    def _compute_project_task_count(self):
        for record in self:
            record.x_project_task_count = record.x_project_id.task_count if record.x_project_id else 0

    def action_create_project_from_lead(self):
        """Create a project from this CRM Lead and copy all relevant fields."""
        self.ensure_one()
        
        if self.x_project_id:
            raise UserError(_("A project has already been created from this opportunity."))
        
        event_id = self.x_event_id
        project_name = self.partner_name or self.contact_name or "Event"
        if event_id:
            project_name = f"{project_name}-{event_id}"
        
        project_vals = {
            "name": project_name,
            "partner_id": self.partner_id.id if self.partner_id else False,
            "user_id": self.user_id.id if self.user_id else False,
            "x_crm_lead_id": self.id,
            "x_event_id": event_id,
            "x_event_type": self.x_event_type,
            "x_event_name": self.x_event_name,
            "x_event_date": self.x_event_date,
            "x_event_time": self.x_event_time,
            "x_guest_count": self.x_estimated_guest_count,
            "x_venue_name": self.x_venue_name,
            "x_total_hours": self.x_total_hours,
            "date_start": self.x_event_date,
        }
        
        project = self.env["project.project"].sudo().create(project_vals)
        self.write({"x_project_id": project.id})
        
        try:
            project.action_create_event_tasks()
            self.message_post(
                body=_("Event tasks created for project: %s") % project.name,
                message_type="notification",
            )
        except Exception as e:
            self.message_post(
                body=_("Project created but error creating tasks: %s") % str(e),
                message_type="notification",
                subtype_xmlid="mail.mt_note",
            )
        
        return {
            "type": "ir.actions.act_window",
            "name": _("Project Created"),
            "res_model": "project.project",
            "res_id": project.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_view_project(self):
        """Open the related project."""
        self.ensure_one()
        if self.x_project_id:
            project = self.x_project_id
        else:
            confirmed_orders = self.order_ids.filtered(lambda so: so.state == 'sale')
            if confirmed_orders:
                projects_from_so = confirmed_orders.mapped('project_ids').filtered(lambda p: p)
                projects_from_crm = self.env['project.project'].search([
                    ('x_crm_lead_id', '=', self.id)
                ], limit=1)
                project = projects_from_so[0] if projects_from_so else projects_from_crm
                if project:
                    self.write({'x_project_id': project.id})
                else:
                    return False
            else:
                return False
        
        return {
            "type": "ir.actions.act_window",
            "name": _("Project"),
            "res_model": "project.project",
            "res_id": project.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_view_project_tasks(self):
        """Open the project tasks."""
        self.ensure_one()
        if not self.x_project_id:
            return False
        return {
            "type": "ir.actions.act_window",
            "name": _("Project Tasks"),
            "res_model": "project.task",
            "view_mode": "list,form,kanban",
            "domain": [("project_id", "=", self.x_project_id.id)],
            "context": {
                "default_project_id": self.x_project_id.id,
                "search_default_project_id": self.x_project_id.id,
            },
        }

    # === INVOICE PAYMENT TRACKING ===
    company_currency = fields.Many2one(
        "res.currency",
        string="Company Currency",
        related="company_id.currency_id",
        store=True,
        readonly=True,
        help="Currency of the company",
    )
    x_invoice_count = fields.Integer(
        string="# Invoices",
        compute="_compute_invoice_payment_data",
        help="Number of invoices linked to this opportunity via sale orders.",
    )
    x_invoice_total = fields.Monetary(
        string="Total Invoice Amount",
        compute="_compute_invoice_payment_data",
        currency_field="company_currency",
        help="Total amount of all invoices.",
    )
    x_invoice_paid = fields.Monetary(
        string="Amount Paid",
        compute="_compute_invoice_payment_data",
        currency_field="company_currency",
        help="Total amount paid across all invoices.",
    )
    x_invoice_remaining = fields.Monetary(
        string="Remaining Balance",
        compute="_compute_invoice_payment_data",
        currency_field="company_currency",
        help="Outstanding balance across all invoices.",
    )
    x_invoice_payment_status = fields.Selection(
        [
            ("not_paid", "Not Paid"),
            ("partial", "Partially Paid"),
            ("paid", "Paid"),
            ("overdue", "Overdue"),
        ],
        string="Payment Status",
        compute="_compute_invoice_payment_data",
        help="Overall payment status based on linked invoices.",
    )

    @api.depends("order_ids.invoice_ids.payment_state", "order_ids.invoice_ids.amount_total", 
                 "order_ids.invoice_ids.amount_residual", "order_ids.invoice_ids.invoice_date_due",
                 "order_ids.invoice_ids.state")
    def _compute_invoice_payment_data(self):
        """Compute invoice payment tracking data from linked sale orders."""
        for lead in self:
            invoices = self.env["account.move"]
            for order in lead.order_ids:
                invoices |= order.invoice_ids.filtered(
                    lambda inv: inv.state == "posted" and inv.move_type == "out_invoice"
                )
            
            lead.x_invoice_count = len(invoices)
            company_currency = lead.company_currency or self.env.company.currency_id
            invoice_total = 0.0
            invoice_remaining = 0.0
            for inv in invoices:
                inv_total = inv.currency_id._convert(
                    inv.amount_total, company_currency, inv.company_id, inv.date or fields.Date.today()
                )
                inv_residual = inv.currency_id._convert(
                    inv.amount_residual, company_currency, inv.company_id, inv.date or fields.Date.today()
                )
                invoice_total += inv_total
                invoice_remaining += inv_residual
            
            lead.x_invoice_total = invoice_total
            lead.x_invoice_remaining = invoice_remaining
            lead.x_invoice_paid = invoice_total - invoice_remaining
            
            if not invoices:
                lead.x_invoice_payment_status = False
            elif all(inv.payment_state == "paid" for inv in invoices):
                lead.x_invoice_payment_status = "paid"
            elif any(inv.payment_state == "paid" for inv in invoices) and any(inv.payment_state != "paid" for inv in invoices):
                lead.x_invoice_payment_status = "partial"
            elif any(inv.invoice_date_due and inv.invoice_date_due < fields.Date.today() and inv.payment_state != "paid" for inv in invoices):
                lead.x_invoice_payment_status = "overdue"
            else:
                lead.x_invoice_payment_status = "not_paid"

    def action_view_invoices(self):
        """Action to view linked invoices (only sent invoices)."""
        self.ensure_one()
        invoices = self.env["account.move"]
        for order in self.order_ids:
            invoices |= order.invoice_ids.filtered(
                lambda inv: inv.state == "posted" and inv.move_type == "out_invoice"
            )
        
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")
        action["domain"] = [("id", "in", invoices.ids)]
        if len(invoices) == 1:
            action["views"] = [(self.env.ref("account.view_move_form").id, "form")]
            action["res_id"] = invoices.id
        return action

    def _merge_get_fields(self):
        """Include x_project_id in merge dependencies."""
        merge_fields = super()._merge_get_fields()
        return merge_fields + ["x_project_id"]
    
    def action_suggest_sale_template(self):
        """Suggest appropriate sale order template based on event type."""
        self.ensure_one()
        if not self.x_event_type:
            return False
        
        template_mapping = {
            "private_wedding": "ptt_business_core.sale_order_template_wedding",
            "corporate_conference": "ptt_business_core.sale_order_template_corporate",
            "corporate_groundbreaking": "ptt_business_core.sale_order_template_corporate",
            "corporate_ribbon_cutting": "ptt_business_core.sale_order_template_corporate",
            "corporate_product_launch": "ptt_business_core.sale_order_template_corporate",
            "corporate_awards": "ptt_business_core.sale_order_template_corporate",
            "corporate_team_building": "ptt_business_core.sale_order_template_team_building",
            "corporate_holiday": "ptt_business_core.sale_order_template_corporate",
            "private_luxury": "ptt_business_core.sale_order_template_private",
            "private_graduation": "ptt_business_core.sale_order_template_private",
            "private_reunion": "ptt_business_core.sale_order_template_private",
            "private_cultural": "ptt_business_core.sale_order_template_private",
            "private_barmitzvah": "ptt_business_core.sale_order_template_private",
            "private_desi": "ptt_business_core.sale_order_template_private",
            "private_quinceanera": "ptt_business_core.sale_order_template_private",
            "private_birthday": "ptt_business_core.sale_order_template_private",
            "community_hoa": "ptt_business_core.sale_order_template_community",
            "community_cities_schools": "ptt_business_core.sale_order_template_community",
            "community_festivals": "ptt_business_core.sale_order_template_community",
            "community_pool_party": "ptt_business_core.sale_order_template_community",
            "community_holiday": "ptt_business_core.sale_order_template_community",
            "community_movie_night": "ptt_business_core.sale_order_template_community",
            "community_vendor_fair": "ptt_business_core.sale_order_template_community",
            "charity_banquet": "ptt_business_core.sale_order_template_community",
            "charity_race": "ptt_business_core.sale_order_template_community",
            "charity_awareness": "ptt_business_core.sale_order_template_community",
            "charity_donor": "ptt_business_core.sale_order_template_community",
            "themed_casino": "ptt_business_core.sale_order_template_private",
            "themed_watch_party": "ptt_business_core.sale_order_template_private",
            "themed_sports": "ptt_business_core.sale_order_template_private",
            "themed_decade": "ptt_business_core.sale_order_template_private",
            "themed_masquerade": "ptt_business_core.sale_order_template_private",
            "themed_cigar_whiskey": "ptt_business_core.sale_order_template_private",
        }
        
        template_xmlid = template_mapping.get(self.x_event_type)
        if template_xmlid:
            template = self.env.ref(template_xmlid, raise_if_not_found=False)
            if template:
                return template.id
        
        return False
