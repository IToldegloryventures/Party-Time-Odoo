from odoo import models, fields, api, _
from odoo.exceptions import UserError


class CrmLead(models.Model):
    """Extend CRM Lead for PTT event management.
    
    NOTE: Use standard Odoo fields where possible:
    - user_id = Sales Rep (standard)
    - contact_name = Contact Name (standard)
    - partner_name = Company Name (standard)
    - phone = Phone Number (standard)
    - email_from = Email Address (standard)
    - description = Additional Notes (standard)
    - source_id = Lead Source (standard - use instead of custom inquiry_source)
    - expected_revenue = Budget (standard - use instead of custom budget_range)
    - name = Opportunity Name / Event Name (standard)
    
    Use Activities for follow-ups instead of custom boolean fields.
    Use Stages for tracking proposal/contract status.
    
    FIELD NAMING:
    - All custom fields use ptt_ prefix (Party Time Texas)
    - This follows Odoo best practice: x_ is reserved for Studio fields
    - Reference: https://www.odoo.com/documentation/19.0/developer/reference/backend/orm.html
    """
    _inherit = "crm.lead"

    # === TIER 1: ADDITIONAL CONTACT INFORMATION ===
    ptt_date_of_call = fields.Date(
        string="Date of Call",
        help="Date of the initial inquiry call.",
    )
    ptt_preferred_contact_method = fields.Selection(
        [
            ("call", "Phone Call"),
            ("text", "Text Message"),
            ("email", "Email"),
        ],
        string="Preferred Contact Method",
    )
    ptt_second_poc_name = fields.Char(string="2nd POC Name")
    ptt_second_poc_phone = fields.Char(string="2nd POC Phone")
    ptt_second_poc_email = fields.Char(string="2nd POC Email")

    # === EVENT ID (Manual Entry - Links CRM, SO, Project, Tasks) ===
    ptt_event_id = fields.Char(
        string="Event ID",
        copy=False,
        index=True,
        tracking=True,
        help="Unique event identifier. Enter manually to link this opportunity with its Project and Tasks.",
    )

    ptt_referral_source = fields.Char(
        string="Referral Details",
        help="If referral, who referred this client? (Use source_id for lead source type)",
    )

    # === EVENT OVERVIEW ===
    ptt_event_type = fields.Selection(
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
    ptt_event_specific_goal = fields.Char(string="Specific Goal")
    ptt_event_date = fields.Date(string="Event Date", index=True)
    ptt_event_time = fields.Char(string="Event Time")
    ptt_total_hours = fields.Float(string="Total Hours")
    ptt_estimated_guest_count = fields.Integer(string="Estimated Guest Count")
    ptt_venue_booked = fields.Boolean(string="Venue Booked?")
    ptt_venue_name = fields.Char(string="Venue")
    ptt_event_location_type = fields.Selection(
        [
            ("indoor", "Indoor"),
            ("outdoor", "Outdoor"),
            ("combination", "Combination"),
        ],
        string="Event Location",
    )

    # === SERVICES REQUESTED (CHECKBOXES) ===
    ptt_service_dj = fields.Boolean(string="DJ & MC Services")
    ptt_service_photovideo = fields.Boolean(string="Photo/Video")
    ptt_service_live_entertainment = fields.Boolean(string="Live Entertainment")
    ptt_service_lighting = fields.Boolean(string="Lighting/AV")
    ptt_service_decor = fields.Boolean(string="Decor/Thematic Design")
    ptt_service_venue_sourcing = fields.Boolean(string="Venue Sourcing")
    ptt_service_catering = fields.Boolean(string="Catering & Bartender Services")
    ptt_service_transportation = fields.Boolean(string="Transportation")
    ptt_service_rentals = fields.Boolean(string="Rentals (Other)")
    ptt_service_photobooth = fields.Boolean(string="Photo Booth")
    ptt_service_caricature = fields.Boolean(string="Caricature Artist")
    ptt_service_casino = fields.Boolean(string="Casino Services")
    ptt_service_staffing = fields.Boolean(string="Staffing")

    # === CFO/FINANCE CONTACT (for corporate clients) ===
    ptt_cfo_name = fields.Char(string="CFO/Finance Contact Name")
    ptt_cfo_phone = fields.Char(string="CFO/Finance Contact Phone")
    ptt_cfo_email = fields.Char(string="CFO/Finance Contact Email")
    ptt_cfo_contact_method = fields.Selection(
        [
            ("call", "Phone Call"),
            ("text", "Text Message"),
            ("email", "Email"),
        ],
        string="CFO Preferred Contact Method",
    )


    # === SERVICE LINES (Vendor Tab) ===
    ptt_service_line_ids = fields.One2many(
        "ptt.crm.service.line",
        "lead_id",
        string="Service Lines",
        help="Services requested for this event with tier selection",
    )

    # === VENDOR ASSIGNMENTS (Vendor Tab) ===
    ptt_vendor_assignment_ids = fields.One2many(
        "ptt.crm.vendor.assignment",
        "lead_id",
        string="Vendor Assignments",
        help="Vendors assigned to provide services for this event",
    )

    # === ACTION METHODS ===

    def action_view_sale_orders(self):
        """Open linked Sale Orders."""
        self.ensure_one()
        if not self.order_ids:
            return False
        if len(self.order_ids) == 1:
            return {
                "type": "ir.actions.act_window",
                "name": _("Sale Order"),
                "res_model": "sale.order",
                "res_id": self.order_ids.id,
                "view_mode": "form",
                "target": "current",
            }
        return {
            "type": "ir.actions.act_window",
            "name": _("Sale Orders"),
            "res_model": "sale.order",
            "view_mode": "tree,form",
            "domain": [("id", "in", self.order_ids.ids)],
            "target": "current",
        }

    def action_view_invoices(self):
        """Action to view linked invoices (via sale orders)."""
        self.ensure_one()
        invoices = self.env["account.move"]
        for order in self.order_ids:
            invoices |= order.invoice_ids.filtered(
                lambda inv: inv.state == "posted" and inv.move_type == "out_invoice"
            )
        
        if not invoices:
            return False
        
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")
        action["domain"] = [("id", "in", invoices.ids)]
        if len(invoices) == 1:
            action["views"] = [(self.env.ref("account.view_move_form").id, "form")]
            action["res_id"] = invoices.id
        return action
    
    def action_suggest_sale_template(self):
        """Suggest appropriate sale order template based on event type."""
        self.ensure_one()
        if not self.ptt_event_type:
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
        
        template_xmlid = template_mapping.get(self.ptt_event_type)
        if template_xmlid:
            template = self.env.ref(template_xmlid, raise_if_not_found=False)
            if template:
                return template.id
        
        return False
