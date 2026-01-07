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
    
    # Store secondary SR from partner for reference on leads
    x_secondary_sales_rep_id = fields.Many2one(
        "res.users",
        string="Secondary Sales Rep",
        help="Secondary sales rep pulled from the contact record.",
        domain="[('share', '=', False)]",
    )
    
    @api.onchange("partner_id")
    def _onchange_partner_id_sales_rep(self):
        """Auto-populate sales rep from partner's assigned Primary SR.
        
        When a repeat customer comes into CRM:
        1. Find matching company/contact (partner_id)
        2. Pull primary sales rep if assigned on contact
        3. Pull secondary sales rep for reference
        """
        if self.partner_id:
            # Check if partner has a primary sales rep assigned
            if self.partner_id.x_primary_sales_rep_id:
                # Only update if user_id is not already set (don't override manual selection)
                if not self.user_id:
                    self.user_id = self.partner_id.x_primary_sales_rep_id
            
            # Also pull secondary SR for reference
            if self.partner_id.x_secondary_sales_rep_id:
                self.x_secondary_sales_rep_id = self.partner_id.x_secondary_sales_rep_id
            
            # Also check the commercial partner (parent company) if individual contact
            if not self.user_id and self.partner_id.commercial_partner_id != self.partner_id:
                commercial = self.partner_id.commercial_partner_id
                if commercial.x_primary_sales_rep_id:
                    self.user_id = commercial.x_primary_sales_rep_id
                if commercial.x_secondary_sales_rep_id and not self.x_secondary_sales_rep_id:
                    self.x_secondary_sales_rep_id = commercial.x_secondary_sales_rep_id
    
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

    x_inquiry_source = fields.Selection(
        [
            ("web_form", "Web Form"),
            ("phone", "Phone Call"),
            ("email", "Email"),
            ("referral", "Referral"),
            ("walk_in", "Walk-In"),
            ("social_media", "Social Media"),
        ],
        string="Inquiry Source",
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
        string="Event Type",
    )
    x_event_name = fields.Char(string="Event Name (if known)")
    x_event_specific_goal = fields.Char(string="Specific Goal")
    x_event_date = fields.Date(string="Event Date")
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

    # === TIER 2: SERVICES REQUESTED (CHECKBOXES) ===
    x_service_dj = fields.Boolean(string="DJ/MC Services")
    x_service_photovideo = fields.Boolean(string="Photo/Video")
    
    # === TIER 2: DJ/MC SERVICE QUESTIONS (visible when x_service_dj = True) ===
    x_dj_event_type = fields.Selection(
        [
            ("wedding", "Wedding"),
            ("corporate", "Corporate"),
            ("birthday", "Birthday"),
            ("anniversary", "Anniversary"),
            ("graduation", "Graduation"),
            ("holiday", "Holiday"),
            ("other", "Other"),
        ],
        string="DJ Event Type",
    )
    x_dj_guest_age_range = fields.Char(string="DJ Guest Age Range")
    x_dj_guest_count = fields.Integer(string="DJ Expected Guest Count")
    x_dj_music_styles = fields.Text(string="Desired Music Styles")
    x_dj_family_friendly = fields.Boolean(string="Family-Friendly Event?")
    x_dj_multi_part_event = fields.Boolean(string="DJ Multi-Part Event? (e.g. Ceremony + Reception)")
    x_dj_multi_location = fields.Boolean(string="Multi-Location Event?")
    x_dj_split_time = fields.Boolean(string="DJ Split Time?")
    x_dj_split_equipment = fields.Boolean(string="DJ Split Equipment?")
    x_dj_mc_needed = fields.Boolean(string="MC Needed? (vs. DJ as music-only)")
    x_dj_karaoke_desired = fields.Boolean(string="Karaoke Desired?")
    x_dj_karaoke_duration = fields.Char(string="Karaoke Duration (if yes)")
    x_dj_karaoke_separate_system = fields.Boolean(string="Karaoke Separate System?")
    x_dj_karaoke_song_list_options = fields.Text(string="Karaoke Song List Options")
    x_dj_lighting_included = fields.Boolean(string="Lighting Included or Needed?")
    x_dj_mic_required = fields.Boolean(string="Microphone Required for Speakers/Toasts?")
    x_dj_venue_setup = fields.Selection(
        [
            ("indoor", "Indoors"),
            ("outdoor", "Outdoors"),
            ("mixed", "Mixed"),
        ],
        string="DJ Venue Setup",
    )
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

    # === TIER 2: AUDIO/VISUAL SERVICES QUESTIONS (visible when x_service_lighting = True) ===
    x_av_event_type = fields.Char(string="Type of Event (AV)")
    x_av_purpose = fields.Selection(
        [
            ("presentation", "Presentation"),
            ("entertainment", "Entertainment"),
            ("ambiance", "Ambiance"),
            ("combination", "Combination"),
        ],
        string="Purpose of AV Services",
    )
    x_av_media_format = fields.Selection(
        [
            ("powerpoint", "PowerPoint"),
            ("video", "Video"),
            ("livestream", "Livestream"),
            ("other", "Other"),
        ],
        string="Format of Media",
    )
    x_av_venue_size = fields.Char(string="Size of Venue")
    x_av_attendee_count = fields.Integer(string="Number of Attendees (AV)")
    x_av_projection_led_needed = fields.Selection(
        [
            ("projection", "Projection"),
            ("led_screen", "LED Screen"),
            ("both", "Both"),
            ("neither", "Neither"),
        ],
        string="Projection or LED Screen Needed?",
    )
    x_av_microphones_needed = fields.Boolean(string="Microphones Needed?")
    x_av_mic_count = fields.Integer(string="How Many Microphones?")
    x_av_lighting_type = fields.Selection(
        [
            ("stage", "Stage Lighting"),
            ("ambient", "Ambient Lighting"),
            ("both", "Both"),
            ("neither", "Neither"),
        ],
        string="Stage Lighting or Ambient Lighting?",
    )
    x_av_content_type = fields.Selection(
        [
            ("logos", "Logos"),
            ("video_montage", "Video Montage"),
            ("realtime_feed", "Real-Time Feed"),
            ("other", "Other"),
        ],
        string="Type of Content to Display",
    )
    x_av_technical_support_needed = fields.Boolean(string="Technical Support Needed On-Site?")
    x_av_support_type = fields.Text(string="What Type of Support Does Vendor Provide?")
    x_av_livestream_needed = fields.Boolean(string="Live Streaming Needed?")
    x_av_location_type = fields.Selection(
        [
            ("indoor", "Indoor"),
            ("outdoor", "Outdoor"),
        ],
        string="Indoor or Outdoor (AV)?",
    )
    x_av_integrated_stage_band = fields.Boolean(string="Will This Be Integrated with Stage or Band?")

    # === TIER 2: FACE PAINTERS/AIRBRUSH TATTOOS QUESTIONS (visible when service selected) ===
    x_facepaint_event_type = fields.Char(string="Type of Event (Face Paint)")
    x_facepaint_guest_age_range = fields.Char(string="Face Paint Guest Age Range")
    x_facepaint_total_attendees = fields.Integer(string="Total Expected Attendees")
    x_facepaint_location_type = fields.Selection(
        [
            ("indoor", "Indoor"),
            ("outdoor", "Outdoor"),
        ],
        string="Indoor or Outdoor (Face Paint)?",
    )
    x_facepaint_style = fields.Selection(
        [
            ("face_paint", "Face Paint"),
            ("airbrush_tattoos", "Airbrush Tattoos"),
            ("henna", "Henna"),
            ("combo", "Combo"),
        ],
        string="Desired Style",
    )
    x_facepaint_artist_count = fields.Integer(string="How Many Artists Needed?")
    x_facepaint_theme_based = fields.Boolean(string="Theme-Based Design Requested?")
    x_facepaint_duration = fields.Char(string="Duration of Service")

    # === TIER 2: PHOTO BOOTH RENTALS QUESTIONS (visible when service selected) ===
    x_photobooth_type = fields.Selection(
        [
            ("360", "360 Booth"),
            ("standard", "Standard Booth"),
            ("ai", "AI Booth"),
            ("green_screen", "Green Screen"),
            ("other", "Other"),
        ],
        string="Type of Booth Desired",
    )
    x_photobooth_event_type = fields.Char(string="Event Type (Photo Booth)")
    x_photobooth_theme = fields.Char(string="Theme")
    x_photobooth_guest_count = fields.Integer(string="Number of Expected Guests (Photo Booth)")
    x_photobooth_location_type = fields.Selection(
        [
            ("indoor", "Indoor"),
            ("outdoor", "Outdoor"),
        ],
        string="Indoor or Outdoor Setup?",
    )
    x_photobooth_delivery_method = fields.Selection(
        [
            ("print", "Print"),
            ("digital_text", "Digital - Text"),
            ("digital_email", "Digital - Email"),
            ("both", "Both"),
        ],
        string="Print or Digital Delivery?",
    )
    x_photobooth_runtime_duration = fields.Char(string="Duration of Booth Runtime")
    x_photobooth_custom_branding = fields.Boolean(string="Photo Booth Custom Branding or Overlay Graphics?")
    x_photobooth_attendant_required = fields.Boolean(string="Will an Attendant Be Required?")
    x_photobooth_wifi_access = fields.Boolean(string="Wi-Fi Access (for Instant Sharing)?")

    # === TIER 2: CARICATURE ARTISTS QUESTIONS (visible when service selected) ===
    x_caricature_event_type = fields.Char(string="Event Type (Caricature)")
    x_caricature_location = fields.Char(string="Location")
    x_caricature_drawing_type = fields.Selection(
        [
            ("hand_drawn", "Hand-Drawn"),
            ("digital", "Digital"),
        ],
        string="Hand-Drawn or Digital?",
    )
    x_caricature_wifi_availability = fields.Boolean(string="WiFi Availability?")
    x_caricature_power_availability = fields.Boolean(string="Power Availability?")
    x_caricature_style_preference = fields.Selection(
        [
            ("humorous", "Humorous"),
            ("realistic", "Realistic"),
            ("themed", "Themed"),
        ],
        string="Style Preference",
    )
    x_caricature_guest_count = fields.Integer(string="Number of Guests Expected (Caricature)")
    x_caricature_drawing_hours = fields.Float(string="Hours of Drawing Time Needed")
    x_caricature_artist_count = fields.Integer(string="Number of Artists Requested")
    x_caricature_location_type = fields.Selection(
        [
            ("indoor", "Indoor"),
            ("outdoor", "Outdoor"),
        ],
        string="Indoor or Outdoor (Caricature)?",
    )
    x_caricature_custom_branding = fields.Boolean(string="Caricature Custom Branding or Overlay Graphics?")

    # === TIER 2: CASINO-THEMED EVENTS QUESTIONS (visible when service selected) ===
    x_casino_event_type = fields.Char(string="Event Type (Casino)")
    x_casino_player_count = fields.Integer(string="Number of Players Expected")
    x_casino_desired_games = fields.Text(string="Desired Games (Blackjack, Roulette, Craps, etc.)")
    x_casino_chip_redemption = fields.Selection(
        [
            ("prizes", "Chips Redeemed for Prizes"),
            ("play_for_fun", "Play-for-Fun Only"),
        ],
        string="Will Chips Be Redeemed for Prizes or Play-for-Fun?",
    )
    x_casino_funny_money_provider = fields.Selection(
        [
            ("customer", "Customer Providing"),
            ("vendor", "Vendor Providing"),
        ],
        string="Is Customer Providing or Vendor Providing FUNNY Money?",
    )
    x_casino_duration = fields.Char(string="Duration of Play")
    x_casino_location_type = fields.Selection(
        [
            ("indoor", "Indoors"),
            ("outdoor", "Outdoors"),
        ],
        string="Indoors or Outdoors?",
    )

    # === TIER 2: BANDS/MUSICIANS QUESTIONS (visible when x_service_live_entertainment = True) ===
    x_band_type = fields.Char(string="Type of Band or Musical Act")
    x_band_event_type = fields.Char(string="Event Type (Band)")
    x_band_guest_demographic = fields.Char(string="Guest Demographic")
    x_band_music_style = fields.Text(string="Style of Music")
    x_band_location_type = fields.Selection(
        [
            ("indoor", "Indoor"),
            ("outdoor", "Outdoor"),
        ],
        string="Indoor or Outdoor (Band)?",
    )
    x_band_multi_part_event = fields.Boolean(string="Band Multi-Part Event? (e.g. Ceremony + Reception)")
    x_band_multi_location = fields.Boolean(string="Multi Location Event?")
    x_band_split_time = fields.Boolean(string="Band Split Time?")
    x_band_split_equipment = fields.Boolean(string="Band Split Equipment?")
    x_band_sets_hours = fields.Char(string="How Many Sets or Hours Needed?")
    x_band_performance_area_size = fields.Char(string="Size of Performance Area")
    x_band_stage_required = fields.Boolean(string="Stage Required?")
    x_band_stage_size = fields.Text(string="What Size Stage, etc.?")
    x_band_dressing_room_available = fields.Boolean(string="Is a Dressing Room Available?")

    # === TIER 2: EVENT COORDINATION SERVICES QUESTIONS (visible when service selected) ===
    x_coordination_event_type = fields.Char(string="Type of Event (Coordination)")
    x_coordination_event_dates = fields.Char(string="Event Date(s)")
    x_coordination_event_locations = fields.Text(string="Event Location(s)")
    x_coordination_service_level = fields.Selection(
        [
            ("day_of", "Day-of"),
            ("full_planning", "Full Planning"),
            ("partial", "Partial"),
        ],
        string="What Level of Service Is Needed?",
    )
    x_coordination_services_booked = fields.Text(string="What Services Are Already Booked vs Still Needed?")
    x_coordination_venue_vendor_contracts = fields.Boolean(string="Are Venue/Vendor Contracts Already in Place?")
    x_coordination_contract_details = fields.Text(string="If Yes - Provide Contract Details")
    x_coordination_vendor_count = fields.Integer(string="Expected Number of Vendors to Manage?")
    x_coordination_responsibilities = fields.Text(string="High Level List of Responsibilities for Coordinator")

    # === FOLLOW-UP INFORMATION ===
    x_followup_email_sent = fields.Boolean(string="Follow-up Email Sent?")
    x_proposal_sent = fields.Boolean(string="Proposal Sent?")
    x_next_contact_date = fields.Date(string="Next Scheduled Contact Date")
    # NOTE: Additional Notes uses standard 'description' field (Html field on Notes tab)

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

    # === EVENT PRICING (ESTIMATED) ===
    x_vendor_estimate_ids = fields.One2many(
        "ptt.crm.vendor.estimate",
        "crm_lead_id",
        string="Vendor Cost Estimates",
        help="Estimated vendor costs for this opportunity.",
    )
    company_currency = fields.Many2one(
        "res.currency",
        string="Company Currency",
        related="company_id.currency_id",
        store=True,
        readonly=True,
        help="Currency of the company",
    )
    x_estimated_total_vendor_costs = fields.Monetary(
        string="Total Estimated Vendor Costs",
        compute="_compute_pricing_totals",
        currency_field="company_currency",
        store=True,
        help="Sum of all estimated vendor costs.",
    )
    x_estimated_client_total = fields.Monetary(
        string="Estimated Client Total",
        currency_field="company_currency",
        help="Total amount client will pay (estimated).",
    )
    x_estimated_margin = fields.Monetary(
        string="Estimated Margin",
        compute="_compute_pricing_totals",
        currency_field="company_currency",
        store=True,
        help="Estimated margin = Client Total - Vendor Costs.",
    )
    x_estimated_margin_percent = fields.Float(
        string="Estimated Margin %",
        compute="_compute_pricing_totals",
        store=True,
        help="Estimated margin percentage.",
    )
    
    # === ACTUAL MARGIN (from related project) ===
    x_actual_client_total = fields.Monetary(
        string="Actual Client Total",
        compute="_compute_actual_margin",
        currency_field="company_currency",
        store=True,
        help="Actual client total from related project (uses accounting data if available, otherwise project fields).",
    )
    x_actual_total_vendor_costs = fields.Monetary(
        string="Actual Total Vendor Costs",
        compute="_compute_actual_margin",
        currency_field="company_currency",
        store=True,
        help="Actual vendor costs from related project.",
    )
    x_actual_margin = fields.Monetary(
        string="Actual Margin",
        compute="_compute_actual_margin",
        currency_field="company_currency",
        store=True,
        help="Actual margin from related project (most accurate when project has accounting data).",
    )
    x_actual_margin_percent = fields.Float(
        string="Actual Margin %",
        compute="_compute_actual_margin",
        store=True,
        help="Actual margin percentage from related project (most accurate when project has accounting data).",
    )

    @api.depends("x_vendor_estimate_ids.estimated_cost", "x_estimated_client_total")
    def _compute_pricing_totals(self):
        """Compute estimated vendor costs, margin, and margin percentage."""
        for lead in self:
            total_vendor_costs = sum(lead.x_vendor_estimate_ids.mapped("estimated_cost"))
            lead.x_estimated_total_vendor_costs = total_vendor_costs
            lead.x_estimated_margin = lead.x_estimated_client_total - total_vendor_costs
            if lead.x_estimated_client_total > 0:
                lead.x_estimated_margin_percent = (lead.x_estimated_margin / lead.x_estimated_client_total) * 100
            else:
                lead.x_estimated_margin_percent = 0.0
    
    @api.depends(
        "order_ids", 
        "order_ids.state", 
        "order_ids.amount_total",
        # Note: project_id dependencies removed because project_id field on sale.order
        # comes from sale_project module which may not be installed. The compute method
        # handles project_id access dynamically via .mapped("project_id").
    )
    def _compute_actual_margin(self):
        """Compute actual margin from confirmed Sale Orders (contracts) using hybrid approach.
        
        Workflow: CRM Lead → Sale Order (Contract) → Project (Execution)
        Revenue comes from confirmed Sale Orders (the signed contracts).
        Costs come from vendor bills/invoices linked to those sale orders or their projects.
        
        Note: Accounting data (vendor bills via analytic_distribution) dependencies are complex
        and not included here. The method queries accounting data directly, so it will recalculate
        when sale orders or projects change, but may not update immediately when bills are posted.
        """
        for lead in self:
            # Get confirmed sale orders (signed contracts) linked to this CRM lead
            confirmed_orders = lead.order_ids.filtered(lambda so: so.state == 'sale')
            
            if not confirmed_orders:
                # No confirmed contracts yet - clear actual values
                lead.x_actual_client_total = 0.0
                lead.x_actual_total_vendor_costs = 0.0
                lead.x_actual_margin = 0.0
                lead.x_actual_margin_percent = 0.0
                continue
            
            # REVENUE: Sum of confirmed sale orders (signed contracts)
            total_revenue = sum(confirmed_orders.mapped("amount_total"))
            
            # COSTS: Vendor bills/invoices linked to sale orders or their projects
            total_costs = 0.0
            
            # Get all projects linked to these sale orders
            projects = confirmed_orders.mapped("project_id").filtered(lambda p: p)
            analytic_account_ids = projects.mapped("account_id").filtered(lambda a: a).ids
            
            if analytic_account_ids:
                # PRIMARY: Use accounting data (vendor bills via analytic_distribution)
                vendor_bill_lines = self.env["account.move.line"].search([
                    ("move_id.move_type", "in", ["in_invoice", "in_refund"]),
                    ("move_id.state", "=", "posted"),  # Only posted bills
                    ("analytic_distribution", "in", analytic_account_ids)
                ])
                
                # Get unique vendor bills and sum their totals (avoid double-counting)
                vendor_bills = vendor_bill_lines.mapped("move_id")
                for bill in vendor_bills:
                    if bill.move_type == "in_invoice":
                        total_costs += bill.amount_total
                    elif bill.move_type == "in_refund":
                        total_costs -= bill.amount_total
                
                # If no accounting data found, fall back to project fields
                if total_costs == 0.0:
                    total_costs = sum(projects.mapped("x_actual_total_vendor_costs"))
            else:
                # FALLBACK: Use project fields (no analytic accounts)
                total_costs = sum(projects.mapped("x_actual_total_vendor_costs"))
            
            # Set the computed values
            lead.x_actual_client_total = total_revenue
            lead.x_actual_total_vendor_costs = total_costs
            lead.x_actual_margin = total_revenue - total_costs
            
            # Calculate margin percentage
            if total_revenue > 0:
                lead.x_actual_margin_percent = ((total_revenue - total_costs) / total_revenue) * 100
            else:
                lead.x_actual_margin_percent = 0.0

    # Link to related project (if created)
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

    @api.depends("x_project_id")
    def _compute_project_count(self):
        for record in self:
            record.project_count = 1 if record.x_project_id else 0

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
        
        # Generate Event ID (000001 format)
        last_project = self.env["project.project"].search(
            [("x_event_id", "!=", False)], order="x_event_id desc", limit=1
        )
        if last_project and last_project.x_event_id:
            try:
                next_id = int(last_project.x_event_id) + 1
            except ValueError:
                next_id = 1
        else:
            next_id = 1
        event_id = f"{next_id:06d}"
        
        # Build project name: PartnerName-EventID
        project_name = self.partner_name or self.contact_name or "Unknown"
        project_name = f"{project_name}-{event_id}"
        
        # Map CRM Lead fields to Project fields
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
            "date_start": self.x_event_date,  # Project start date
        }
        
        # Create project
        project = self.env["project.project"].create(project_vals)
        
        # Link project back to lead
        self.write({"x_project_id": project.id})
        
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
        if not self.x_project_id:
            return False
        return {
            "type": "ir.actions.act_window",
            "name": _("Project"),
            "res_model": "project.project",
            "res_id": self.x_project_id.id,
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
        """Compute invoice payment tracking data from linked sale orders.
        Only includes invoices that have been sent (posted state)."""
        for lead in self:
            # Get all SENT invoices from linked sale orders (posted = sent to customer)
            invoices = self.env["account.move"]
            for order in lead.order_ids:
                invoices |= order.invoice_ids.filtered(
                    lambda inv: inv.state == "posted" and inv.move_type == "out_invoice"
                )
            
            lead.x_invoice_count = len(invoices)
            # Convert to company currency for accurate totals
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
            
            # Determine payment status
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
        """Suggest appropriate sale order template based on event type.
        
        Returns the template ID that best matches the event type.
        This can be used when creating a sale order from the CRM lead.
        """
        self.ensure_one()
        if not self.x_event_type:
            return False
        
        # Map event types to sale order templates
        template_mapping = {
            # Wedding events
            "private_wedding": "ptt_business_core.sale_order_template_wedding",
            # Corporate events
            "corporate_conference": "ptt_business_core.sale_order_template_corporate",
            "corporate_groundbreaking": "ptt_business_core.sale_order_template_corporate",
            "corporate_ribbon_cutting": "ptt_business_core.sale_order_template_corporate",
            "corporate_product_launch": "ptt_business_core.sale_order_template_corporate",
            "corporate_awards": "ptt_business_core.sale_order_template_corporate",
            "corporate_team_building": "ptt_business_core.sale_order_template_team_building",
            "corporate_holiday": "ptt_business_core.sale_order_template_corporate",
            # Private events
            "private_luxury": "ptt_business_core.sale_order_template_private",
            "private_graduation": "ptt_business_core.sale_order_template_private",
            "private_reunion": "ptt_business_core.sale_order_template_private",
            "private_cultural": "ptt_business_core.sale_order_template_private",
            "private_barmitzvah": "ptt_business_core.sale_order_template_private",
            "private_desi": "ptt_business_core.sale_order_template_private",
            "private_quinceanera": "ptt_business_core.sale_order_template_private",
            "private_birthday": "ptt_business_core.sale_order_template_private",
            # Community events
            "community_hoa": "ptt_business_core.sale_order_template_community",
            "community_cities_schools": "ptt_business_core.sale_order_template_community",
            "community_festivals": "ptt_business_core.sale_order_template_community",
            "community_pool_party": "ptt_business_core.sale_order_template_community",
            "community_holiday": "ptt_business_core.sale_order_template_community",
            "community_movie_night": "ptt_business_core.sale_order_template_community",
            "community_vendor_fair": "ptt_business_core.sale_order_template_community",
            # Charity events
            "charity_banquet": "ptt_business_core.sale_order_template_community",
            "charity_race": "ptt_business_core.sale_order_template_community",
            "charity_awareness": "ptt_business_core.sale_order_template_community",
            "charity_donor": "ptt_business_core.sale_order_template_community",
            # Themed events - default to private
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

