import re

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

# Time format pattern for HH:MM validation
# Reference: https://www.odoo.com/documentation/19.0/developer/reference/backend/orm.html#method-decorators
TIME_PATTERN = re.compile(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$')


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
        help="Client's preferred method of communication for follow-ups and updates."
    )
    ptt_second_poc_name = fields.Char(
        string="2nd POC Name",
        help="Name of the secondary point of contact for this event."
    )
    ptt_second_poc_phone = fields.Char(
        string="2nd POC Phone",
        help="Phone number of the secondary point of contact."
    )
    ptt_second_poc_email = fields.Char(
        string="2nd POC Email",
        help="Email address of the secondary point of contact."
    )

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
        help="Type of event being planned. Used for categorization, reporting, and template selection."
    )
    ptt_event_specific_goal = fields.Char(
        string="Specific Goal",
        help="Primary objective or goal for this event (e.g., celebration, corporate meeting, fundraiser, team building)."
    )
    ptt_event_date = fields.Date(
        string="Event Date",
        index=True,
        help="Scheduled date for the event. Used for calendar views and event planning."
    )
    ptt_event_time = fields.Char(
        string="Event Time",
        help="Scheduled start time for the event in HH:MM format (e.g., 14:00 for 2:00 PM)."
    )
    ptt_total_hours = fields.Float(
        string="Total Hours",
        default=0.0,
        help="Total duration of the event in hours (e.g., 4.5 for 4 hours 30 minutes). Used for pricing and scheduling."
    )
    ptt_estimated_guest_count = fields.Integer(
        string="Estimated Guest Count",
        default=0,
        help="Expected number of guests/attendees for the event. Used to calculate per-person pricing and resource planning."
    )
    ptt_venue_booked = fields.Boolean(
        string="Venue Booked?",
        default=False,
        help="Indicates whether a specific venue has already been booked for this event."
    )
    ptt_venue_name = fields.Char(
        string="Venue",
        help="Name of the venue where the event will be held (if known or booked)."
    )
    ptt_event_location_type = fields.Selection(
        [
            ("indoor", "Indoor"),
            ("outdoor", "Outdoor"),
            ("combination", "Combination"),
        ],
        string="Event Location",
        help="Type of location for the event. Affects equipment needs and weather contingency planning."
    )

    # === CFO/FINANCE CONTACT (for corporate clients) ===
    ptt_cfo_name = fields.Char(
        string="CFO/Finance Contact Name",
        help="Name of the Chief Financial Officer or finance contact person for approval and payment processing."
    )
    ptt_cfo_phone = fields.Char(
        string="CFO/Finance Contact Phone",
        help="Phone number of the CFO or finance contact person."
    )
    ptt_cfo_email = fields.Char(
        string="CFO/Finance Contact Email",
        help="Email address of the CFO or finance contact person for invoicing and payment communications."
    )
    ptt_cfo_contact_method = fields.Selection(
        [
            ("call", "Phone Call"),
            ("text", "Text Message"),
            ("email", "Email"),
        ],
        string="CFO Preferred Contact Method",
        help="Preferred method of communication for the CFO/finance contact regarding billing and payments."
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

    # === PROJECT LINK (Bidirectional CRM↔Project) ===
    # When SO is confirmed, Odoo creates project via service_tracking.
    # Our custom code links the project back to this CRM lead.
    # Reference: https://www.odoo.com/documentation/19.0/developer/reference/backend/orm.html#relational-fields
    ptt_project_id = fields.Many2one(
        "project.project",
        string="Event Project",
        copy=False,
        help="Project created when this opportunity is booked (SO confirmed).",
    )

    # === CONSTRAINTS ===
    
    @api.constrains('ptt_event_time')
    def _check_event_time_format(self):
        """Validate event time is in HH:MM format.
        
        Reference: https://www.odoo.com/documentation/19.0/developer/reference/backend/orm.html#method-decorators
        Pattern matches Odoo core examples in res_lang.py, res_country.py.
        """
        for record in self:
            if record.ptt_event_time and not TIME_PATTERN.match(record.ptt_event_time):
                raise ValidationError(
                    _("Event Time must be in HH:MM format (e.g., 09:30, 14:00). Got: %s") % record.ptt_event_time
                )
    
    @api.constrains('ptt_estimated_guest_count')
    def _check_guest_count_positive(self):
        """Ensure guest count is not negative.
        
        Reference: https://www.odoo.com/documentation/19.0/developer/reference/backend/orm.html#constraints-and-indexes
        """
        for record in self:
            if record.ptt_estimated_guest_count < 0:
                raise ValidationError(
                    _("Guest count cannot be negative. Got: %s. Please enter 0 or a positive number.") 
                    % record.ptt_estimated_guest_count
                )
    
    @api.constrains('ptt_total_hours')
    def _check_total_hours_positive(self):
        """Ensure event duration is positive.
        
        Reference: https://www.odoo.com/documentation/19.0/developer/reference/backend/orm.html#constraints-and-indexes
        """
        for record in self:
            if record.ptt_total_hours and record.ptt_total_hours <= 0:
                raise ValidationError(
                    _("Event duration must be greater than 0 hours. Got: %s hours. Please enter a positive number.") 
                    % record.ptt_total_hours
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
