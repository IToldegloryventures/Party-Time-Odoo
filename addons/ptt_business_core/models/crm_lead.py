from odoo import models, fields


class CrmLead(models.Model):
    _inherit = "crm.lead"

    # === TIER 1: LEAD CONTACT INFORMATION ===
    x_sales_rep_id = fields.Many2one(
        "res.users",
        string="Sales Rep",
        help="Sales representative handling this lead.",
    )
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
    x_dj_guest_age_range = fields.Char(string="Guest Age Range")
    x_dj_guest_count = fields.Integer(string="DJ Expected Guest Count")
    x_dj_music_styles = fields.Text(string="Desired Music Styles")
    x_dj_family_friendly = fields.Boolean(string="Family-Friendly Event?")
    x_dj_multi_part_event = fields.Boolean(string="Multi-Part Event? (e.g. Ceremony + Reception)")
    x_dj_multi_location = fields.Boolean(string="Multi-Location Event?")
    x_dj_split_time = fields.Boolean(string="Split Time?")
    x_dj_split_equipment = fields.Boolean(string="Split Equipment?")
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
    x_service_rentals = fields.Boolean(string="Rentals")
    x_service_staffing = fields.Boolean(
        string="Staffing (hosts, bartenders, security)"
    )

    # === FOLLOW-UP INFORMATION ===
    x_followup_email_sent = fields.Boolean(string="Follow-up Email Sent?")
    x_proposal_sent = fields.Boolean(string="Proposal Sent?")
    x_next_contact_date = fields.Date(string="Next Scheduled Contact Date")
    x_additional_notes = fields.Text(string="Additional Notes")

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


