import re

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta

# Time format pattern for HH:MM validation
# Reference: https://www.odoo.com/documentation/19.0/developer/reference/backend/orm.html#method-decorators
TIME_PATTERN = re.compile(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$')


class ProjectProject(models.Model):
    """Extend project.project for PTT event management.
    
    NOTE: Use standard Odoo fields where possible:
    - user_id = Project Manager / Sales Rep (standard)
    - partner_id = Client (standard)
    - name = Project/Event Name (standard)
    - sale_order_id = Related Sale Order (from sale_project)
    
    Custom PTT fields are for event-specific data only.
    
    FIELD NAMING:
    - All custom fields use ptt_ prefix (Party Time Texas)
    - This follows Odoo best practice: x_ is reserved for Studio fields
    - Reference: https://www.odoo.com/documentation/19.0/developer/reference/backend/orm.html
    """
    _inherit = "project.project"

    # === VENDOR ASSIGNMENTS (Custom PTT Feature) ===
    ptt_vendor_assignment_ids = fields.One2many(
        "ptt.project.vendor.assignment",
        "project_id",
        string="Vendor Assignments",
        help="Vendor assignments for this project/event.",
    )

    # === CRM LINK (Bidirectional CRM↔Project) ===
    # When SO is confirmed, our custom code links project to CRM lead.
    # Reference: https://www.odoo.com/documentation/19.0/developer/reference/backend/orm.html#relational-fields
    ptt_crm_lead_id = fields.Many2one(
        "crm.lead",
        string="CRM Lead",
        copy=False,
        help="Original CRM lead/opportunity that created this project.",
    )

    # === CLIENT TAB - Computed Fields from CRM Lead ===
    # These fields pull data from the linked CRM lead for the CLIENT tab.
    # CRITICAL: Using computed fields instead of related fields to prevent OwlError
    # when ptt_crm_lead_id is False. Related fields fail when the relation is empty.
    # Reference: https://www.odoo.com/documentation/19.0/developer/reference/backend/orm.html#compute-methods
    ptt_preferred_contact_method = fields.Selection(
        selection=[
            ("call", "Phone Call"),
            ("text", "Text Message"),
            ("email", "Email"),
        ],
        compute="_compute_crm_related_fields",
        readonly=True,
        string="Preferred Contact Method",
        store=False,
    )
    ptt_date_of_call = fields.Date(
        compute="_compute_crm_related_fields",
        readonly=True,
        string="Date of Call",
        store=False,
    )
    ptt_second_poc_name = fields.Char(
        compute="_compute_crm_related_fields",
        readonly=True,
        string="2nd POC Name",
        store=False,
    )
    ptt_second_poc_phone = fields.Char(
        compute="_compute_crm_related_fields",
        readonly=True,
        string="2nd POC Phone",
        store=False,
    )
    ptt_second_poc_email = fields.Char(
        compute="_compute_crm_related_fields",
        readonly=True,
        string="2nd POC Email",
        store=False,
    )
    ptt_venue_booked = fields.Boolean(
        compute="_compute_crm_related_fields",
        readonly=True,
        string="Venue Booked?",
        store=False,
    )
    ptt_cfo_name = fields.Char(
        compute="_compute_crm_related_fields",
        readonly=True,
        string="Finance Contact",
        store=False,
    )
    ptt_cfo_phone = fields.Char(
        compute="_compute_crm_related_fields",
        readonly=True,
        string="Finance Contact Phone",
        store=False,
    )
    ptt_cfo_email = fields.Char(
        compute="_compute_crm_related_fields",
        readonly=True,
        string="Finance Contact Email",
        store=False,
    )
    ptt_cfo_contact_method = fields.Selection(
        selection=[
            ("call", "Phone Call"),
            ("text", "Text Message"),
            ("email", "Email"),
        ],
        compute="_compute_crm_related_fields",
        readonly=True,
        string="Finance Preferred Contact Method",
        store=False,
    )

    # === COMPUTE METHOD FOR CRM RELATED FIELDS ===
    # Safely computes CRM lead fields when ptt_crm_lead_id exists, returns False/empty when missing
    # This prevents OwlError when projects don't have a linked CRM lead
    @api.depends(
        'ptt_crm_lead_id',
        'ptt_crm_lead_id.ptt_preferred_contact_method',
        'ptt_crm_lead_id.ptt_date_of_call',
        'ptt_crm_lead_id.ptt_second_poc_name',
        'ptt_crm_lead_id.ptt_second_poc_phone',
        'ptt_crm_lead_id.ptt_second_poc_email',
        'ptt_crm_lead_id.ptt_venue_booked',
        'ptt_crm_lead_id.ptt_cfo_name',
        'ptt_crm_lead_id.ptt_cfo_phone',
        'ptt_crm_lead_id.ptt_cfo_email',
        'ptt_crm_lead_id.ptt_cfo_contact_method',
    )
    def _compute_crm_related_fields(self):
        """Compute CRM-related fields safely when ptt_crm_lead_id is False.
        
        This prevents OwlError when Owl tries to render Selection fields
        that have undefined metadata when the related record doesn't exist.
        """
        for project in self:
            if project.ptt_crm_lead_id:
                # CRM lead exists - copy values safely
                lead = project.ptt_crm_lead_id
                project.ptt_preferred_contact_method = lead.ptt_preferred_contact_method or False
                project.ptt_date_of_call = lead.ptt_date_of_call or False
                project.ptt_second_poc_name = lead.ptt_second_poc_name or False
                project.ptt_second_poc_phone = lead.ptt_second_poc_phone or False
                project.ptt_second_poc_email = lead.ptt_second_poc_email or False
                project.ptt_venue_booked = lead.ptt_venue_booked or False
                project.ptt_cfo_name = lead.ptt_cfo_name or False
                project.ptt_cfo_phone = lead.ptt_cfo_phone or False
                project.ptt_cfo_email = lead.ptt_cfo_email or False
                project.ptt_cfo_contact_method = lead.ptt_cfo_contact_method or False
            else:
                # No CRM lead - set all to False/empty to prevent OwlError
                project.ptt_preferred_contact_method = False
                project.ptt_date_of_call = False
                project.ptt_second_poc_name = False
                project.ptt_second_poc_phone = False
                project.ptt_second_poc_email = False
                project.ptt_venue_booked = False
                project.ptt_cfo_name = False
                project.ptt_cfo_phone = False
                project.ptt_cfo_email = False
                project.ptt_cfo_contact_method = False

    # === FINANCIALS TAB - Profitability Fields ===
    # These computed fields calculate event profitability for the FINANCIALS tab.
    # Reference: https://www.odoo.com/documentation/19.0/developer/reference/backend/orm.html#compute-methods
    ptt_total_revenue = fields.Monetary(
        string="Total Revenue",
        compute="_compute_profitability",
        store=True,
        currency_field="currency_id",
        help="Total from confirmed sale orders",
    )
    ptt_total_vendor_cost = fields.Monetary(
        string="Total Vendor Cost",
        compute="_compute_profitability",
        store=True,
        currency_field="currency_id",
        help="Sum of all vendor assignment costs",
    )
    ptt_gross_profit = fields.Monetary(
        string="Gross Profit",
        compute="_compute_profitability",
        store=True,
        currency_field="currency_id",
    )
    ptt_profit_margin = fields.Float(
        string="Profit Margin %",
        compute="_compute_profitability",
        store=True,
    )
    ptt_cost_per_guest = fields.Monetary(
        string="Cost Per Guest",
        compute="_compute_profitability",
        store=True,
        currency_field="currency_id",
    )
    ptt_revenue_per_guest = fields.Monetary(
        string="Revenue Per Guest",
        compute="_compute_profitability",
        store=True,
        currency_field="currency_id",
    )

    # === VENDORS TAB - Internal Team Fields ===
    ptt_lead_coordinator_id = fields.Many2one(
        "res.users",
        string="Lead Coordinator",
        help="Primary coordinator for this event",
    )
    ptt_onsite_contact_id = fields.Many2one(
        "res.partner",
        string="Onsite Contact",
        help="Client contact who will be present at event",
    )

    # === EVENT IDENTITY ===
    ptt_event_id = fields.Char(
        string="Event Number",
        copy=False,
        index=True,
        help="Unique event identifier for tracking.",
    )
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
        help="Type of event for categorization and reporting.",
    )

    # === EVENT SCHEDULE ===
    ptt_event_date = fields.Date(
        string="Event Date",
        index=True,
        help="Scheduled event date. Used for calendar views and event planning."
    )
    ptt_event_time = fields.Char(
        string="Event Time",
        help="Scheduled start time for the event in HH:MM format (e.g., 14:00 for 2:00 PM)."
    )
    ptt_guest_count = fields.Integer(
        string="Guest Count",
        default=0,
        help="Actual or confirmed number of guests/attendees for the event. Used for profitability calculations."
    )
    ptt_venue_name = fields.Char(
        string="Venue",
        help="Name of the venue where the event will be held."
    )
    ptt_setup_start_time = fields.Char(
        string="Setup Start Time",
        help="Time when setup should begin in HH:MM format (e.g., 12:00 for noon)."
    )
    ptt_event_start_time = fields.Char(
        string="Event Start Time",
        help="Time when the event officially begins in HH:MM format (e.g., 14:00 for 2:00 PM)."
    )
    ptt_event_end_time = fields.Char(
        string="Event End Time",
        help="Time when the event officially ends in HH:MM format (e.g., 18:00 for 6:00 PM)."
    )
    ptt_total_hours = fields.Float(
        string="Total Hours",
        default=0.0,
        help="Total duration of the event in hours (e.g., 4.5 for 4 hours 30 minutes). Used for pricing and scheduling."
    )
    ptt_teardown_deadline = fields.Char(
        string="Tear-Down Deadline",
        help="Time by which equipment must be removed in HH:MM format (e.g., 20:00 for 8:00 PM)."
    )

    # === EVENT DETAILS ===
    ptt_theme_dress_code = fields.Text(
        string="Theme, Dress Code, or Style Preference",
        help="Event theme, dress code requirements, or style preferences. Used for vendor briefings and event planning."
    )
    ptt_special_requirements_desc = fields.Text(
        string="Special Requirements",
        help="Any special requirements, accommodations, or unique needs for this event (e.g., accessibility, dietary restrictions, equipment needs)."
    )
    ptt_inclement_weather_plan = fields.Text(
        string="Inclement Weather Plan",
        help="Contingency plan for bad weather if this is an outdoor event. Includes backup location, rescheduling policy, or weather protection measures."
    )
    ptt_parking_restrictions_desc = fields.Text(
        string="Parking/Delivery Restrictions",
        help="Parking availability, restrictions, or delivery instructions for vendors. Includes loading dock locations, access times, and parking passes required."
    )

    # === CREATE OVERRIDE (Safety Guard) ===
    
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to ensure company_id and partner_id are always set.
        
        CRITICAL: Prevents frontend OwlError by ensuring required fields are populated.
        Odoo 19 requires company_id for multi-company safety, and partner_id should
        never be undefined (even if set to a fallback value).
        
        Reference: https://www.odoo.com/documentation/19.0/developer/reference/backend/orm.html#creating-records
        """
        # Ensure company_id is set for all records
        for vals in vals_list:
            if not vals.get('company_id'):
                vals['company_id'] = self.env.company.id
            
            # Ensure partner_id is set (use sale order partner, then fallback)
            if not vals.get('partner_id'):
                # Try to get from sale_order_id if provided
                if vals.get('sale_order_id'):
                    sale_order = self.env['sale.order'].browse(vals['sale_order_id'])
                    if sale_order.exists() and sale_order.partner_id:
                        vals['partner_id'] = sale_order.partner_id.id
                        continue
                
                # Try to get from CRM lead if provided
                if vals.get('ptt_crm_lead_id'):
                    lead = self.env['crm.lead'].browse(vals['ptt_crm_lead_id'])
                    if lead.exists() and lead.partner_id:
                        vals['partner_id'] = lead.partner_id.id
                        continue
                
                # Fallback to any existing partner (safer than False or XML ID reference)
                fallback_partner = self.env['res.partner'].search([], limit=1)
                if fallback_partner:
                    vals['partner_id'] = fallback_partner.id
        
        return super().create(vals_list)
    
    # === CONSTRAINTS ===
    
    @api.constrains('ptt_guest_count')
    def _check_guest_count_positive(self):
        """Ensure guest count is not negative.
        
        Reference: https://www.odoo.com/documentation/19.0/developer/reference/backend/orm.html#constraints-and-indexes
        """
        for record in self:
            if record.ptt_guest_count < 0:
                raise ValidationError(
                    _("Guest count cannot be negative. Got: %s. Please enter 0 or a positive number.") 
                    % record.ptt_guest_count
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
    
    @api.constrains('ptt_event_time', 'ptt_setup_start_time', 'ptt_event_start_time', 
                    'ptt_event_end_time', 'ptt_teardown_deadline')
    def _check_time_format(self):
        """Validate all time fields are in HH:MM format.
        
        Reference: https://www.odoo.com/documentation/19.0/developer/reference/backend/orm.html#method-decorators
        Pattern matches Odoo core examples in res_lang.py, res_country.py.
        """
        time_fields = [
            ('ptt_event_time', _("Event Time")),
            ('ptt_setup_start_time', _("Setup Start Time")),
            ('ptt_event_start_time', _("Event Start Time")),
            ('ptt_event_end_time', _("Event End Time")),
            ('ptt_teardown_deadline', _("Tear-Down Deadline")),
        ]
        for record in self:
            for field_name, field_label in time_fields:
                value = record[field_name]
                if value and not TIME_PATTERN.match(value):
                    raise ValidationError(
                        _("%(field)s must be in HH:MM format (e.g., 09:30, 14:00). Got: %(value)s") % {
                            'field': field_label,
                            'value': value,
                        }
                    )

    # === PROFITABILITY COMPUTATION ===
    
    @api.depends(
        "sale_order_id.amount_total",
        "sale_order_id.state",
        "ptt_vendor_assignment_ids.actual_cost",
        "ptt_guest_count",
    )
    def _compute_profitability(self):
        """Compute profitability metrics for FINANCIALS tab.
        
        Calculates:
        - Total revenue from confirmed sale orders
        - Total vendor costs from assignments
        - Gross profit and margin percentage
        - Per-guest metrics
        
        Reference: https://www.odoo.com/documentation/19.0/developer/reference/backend/orm.html#compute-methods
        """
        for project in self:
            # Revenue from sale orders
            revenue = 0.0
            if project.sale_order_id and project.sale_order_id.state == "sale":
                revenue = project.sale_order_id.amount_total
            
            # Vendor costs from assignments
            vendor_cost = sum(
                project.ptt_vendor_assignment_ids.mapped("actual_cost")
            ) if project.ptt_vendor_assignment_ids else 0.0
            
            # Profit calculations
            gross_profit = revenue - vendor_cost
            margin = (gross_profit / revenue * 100) if revenue > 0 else 0.0
            
            # Per guest calculations
            guest_count = project.ptt_guest_count or 0
            cost_per_guest = vendor_cost / guest_count if guest_count > 0 else 0.0
            revenue_per_guest = revenue / guest_count if guest_count > 0 else 0.0
            
            project.update({
                "ptt_total_revenue": revenue,
                "ptt_total_vendor_cost": vendor_cost,
                "ptt_gross_profit": gross_profit,
                "ptt_profit_margin": margin,
                "ptt_cost_per_guest": cost_per_guest,
                "ptt_revenue_per_guest": revenue_per_guest,
            })

    # === TASK CREATION ===
    
    def action_create_event_tasks(self):
        """Button action to create event tasks for this project.
        
        Returns True if tasks were created successfully, False otherwise.
        """
        self.ensure_one()
        try:
            self._create_event_tasks()
            self.message_post(
                body="Event tasks created successfully.",
                message_type="notification",
            )
            return True
        except Exception as e:
            self.message_post(
                body=f"Error creating event tasks: {e}",
                message_type="notification",
            )
            return False

    def _create_event_tasks(self):
        """Auto-create comprehensive event planning tasks for event projects.
        
        Creates 9 standard event tasks:
        1. Confirm Booking with Client
        2. Collect Tier-3 Fulfillment Details
        3. Review Client Deliverables Checklist
        4. Coordinate Vendor Assignments
        5. Vendor Brief & Confirmation
        6. Prepare Event Resources & Logistics
        7. Client Communications & Check-Ins
        8. Final Payment Check & Invoice Follow-up
        9. Post-Event Closure / Review
        """
        self.ensure_one()

        assigned_users = (
            [(6, 0, [self.user_id.id])]
            if self.user_id
            else []
        )

        TaskType = self.env["project.task.type"].sudo()
        todo_type = self.env.ref("ptt_business_core.task_type_todo", raise_if_not_found=False)
        if not todo_type:
            todo_type = TaskType.search([("name", "=", "To Do")], limit=1)
            if not todo_type:
                todo_type = TaskType.create({"name": "To Do"})
        
        Task = self.env["project.task"].sudo()
        
        # Task 1: Confirm Booking with Client
        booking_task = Task.create({
            "name": "Confirm Booking with Client",
            "project_id": self.id,
            "stage_id": todo_type.id,
            "user_ids": assigned_users,
            "description": "Verify contract signed and retainer received",
        })
        
        for sub_task_name in [
            "Verify Retainer has been paid. Verify remaining balance owed.",
            "Send confirmation email stating contract signed + retainer received",
            "Reiterate event date, venue, time, and agreed services",
        ]:
            Task.create({
                "name": sub_task_name,
                "project_id": self.id,
                "parent_id": booking_task.id,
                "stage_id": todo_type.id,
                "user_ids": assigned_users,
            })
        
        # Task 2: Collect Tier-3 Fulfillment Details
        tier3_task = Task.create({
            "name": "Collect Tier-3 Fulfillment Details",
            "project_id": self.id,
            "stage_id": todo_type.id,
            "user_ids": assigned_users,
            "description": "Gather venue access info, rider/equipment specifications, vendor needs, and logistics",
        })
        
        for sub_task_name in [
            "Venue access info (load-in times, restrictions, contacts)",
            "Rider / Equipment Setup specifications",
            "Vendor needs, power, staging, logistics",
            "Special requests (e.g. backup, transportation)",
        ]:
            Task.create({
                "name": sub_task_name,
                "project_id": self.id,
                "parent_id": tier3_task.id,
                "stage_id": todo_type.id,
                "user_ids": assigned_users,
            })
        
        # Task 3: Review Client Deliverables Checklist
        deliverables_task = Task.create({
            "name": "Review Client Deliverables Checklist",
            "project_id": self.id,
            "stage_id": todo_type.id,
            "user_ids": assigned_users,
            "description": "Review and confirm all client-provided deliverables",
        })
        
        for sub_task_name in [
            "Song selections (first dance, special requests)",
            "Timeline (ceremony, reception, breaks)",
            "Venue logistics (floor plan, layout)",
            "Contact point on event day",
            "Guest count confirmation",
        ]:
            Task.create({
                "name": sub_task_name,
                "project_id": self.id,
                "parent_id": deliverables_task.id,
                "stage_id": todo_type.id,
                "user_ids": assigned_users,
            })
        
        # Task 4: Coordinate Vendor Assignments
        vendor_assign_task = Task.create({
            "name": "Coordinate Vendor Assignments",
            "project_id": self.id,
            "stage_id": todo_type.id,
            "user_ids": assigned_users,
            "description": "Assign vendors to event and provide task lists",
        })
        
        for sub_task_name in [
            "Assign vendor(s) to event",
            "Provide vendors with relevant task list, rider info, schedule",
            "Confirm vendors' availability, rates, and contracts",
        ]:
            Task.create({
                "name": sub_task_name,
                "project_id": self.id,
                "parent_id": vendor_assign_task.id,
                "stage_id": todo_type.id,
                "user_ids": assigned_users,
            })
        
        # Task 5: Vendor Brief & Confirmation
        vendor_brief_task = Task.create({
            "name": "Vendor Brief & Confirmation",
            "project_id": self.id,
            "stage_id": todo_type.id,
            "user_ids": assigned_users,
            "description": "Confirm vendor requirements and acceptance",
        })
        
        for sub_task_name in [
            "Confirm vendor requirements for equipment, load-in, contact person",
            "Confirm required documents (COI, contract, tax info)",
            "Confirm vendor acceptance",
        ]:
            Task.create({
                "name": sub_task_name,
                "project_id": self.id,
                "parent_id": vendor_brief_task.id,
                "stage_id": todo_type.id,
                "user_ids": assigned_users,
            })
        
        # Task 6: Prepare Event Resources & Logistics
        resources_task = Task.create({
            "name": "Prepare Event Resources & Logistics",
            "project_id": self.id,
            "stage_id": todo_type.id,
            "user_ids": assigned_users,
            "description": "Prepare inventory, transport, and backup resources",
        })
        
        for sub_task_name in [
            "Inventory / equipment prep",
            "Transport / loading plan",
            "Backup gear / redundancy checks",
            "Power & staging setup plan",
        ]:
            Task.create({
                "name": sub_task_name,
                "project_id": self.id,
                "parent_id": resources_task.id,
                "stage_id": todo_type.id,
                "user_ids": assigned_users,
            })
        
        # Task 7: Client Communications & Check-Ins
        communications_task = Task.create({
            "name": "Client Communications & Check-Ins",
            "project_id": self.id,
            "stage_id": todo_type.id,
            "user_ids": assigned_users,
            "description": "Execute appropriate check-ins and confirm logistics",
        })
        
        for sub_task_name in [
            "Execute appropriate check-ins",
            "Confirm all logistics 1-2 weeks prior",
            "Issue reminders for outstanding client tasks (song lists, special requests)",
        ]:
            Task.create({
                "name": sub_task_name,
                "project_id": self.id,
                "parent_id": communications_task.id,
                "stage_id": todo_type.id,
                "user_ids": assigned_users,
            })
        
        # Task 8: Final Payment Check & Invoice Follow-up
        payment_task = Task.create({
            "name": "Final Payment Check & Invoice Follow-up",
            "project_id": self.id,
            "stage_id": todo_type.id,
            "user_ids": assigned_users,
            "description": "Review invoice balance and confirm full payment status",
        })
        
        for sub_task_name in [
            "Review invoice balance and confirm full payment status",
            "Flag and follow up on unpaid balances",
            "Update system status to Final Payment Received",
        ]:
            Task.create({
                "name": sub_task_name,
                "project_id": self.id,
                "parent_id": payment_task.id,
                "stage_id": todo_type.id,
                "user_ids": assigned_users,
            })
        
        # Task 9: Post-Event Closure / Review
        post_event_deadline = None
        if self.ptt_event_date:
            post_event_deadline = self.ptt_event_date + timedelta(days=1)
        
        post_event_task = Task.create({
            "name": "Post-Event Closure / Review",
            "project_id": self.id,
            "stage_id": todo_type.id,
            "user_ids": assigned_users,
            "date_deadline": post_event_deadline,
            "description": "Confirm event completion and gather feedback",
        })
        
        for sub_task_name in [
            "Confirm event ended as scheduled",
            "Gather client feedback / survey link",
            "Document lessons learned or special notes for future events",
        ]:
            Task.create({
                "name": sub_task_name,
                "project_id": self.id,
                "parent_id": post_event_task.id,
                "stage_id": todo_type.id,
                "user_ids": assigned_users,
            })

    # === SCHEDULED ACTIONS (CRON) ===
    
    @api.model
    def _cron_10day_event_reminder(self):
        """Create 10-day reminder activities for upcoming events.
        
        Runs daily. Finds event projects with ptt_event_date exactly 10 days from today.
        Reference: https://www.odoo.com/documentation/19.0/developer/reference/backend/actions.html
        """
        today = fields.Date.today()
        target_date = today + timedelta(days=10)
        
        projects = self.search([
            ("ptt_event_date", "=", target_date),
        ])
        
        activity_type = self.env.ref(
            "ptt_business_core.activity_type_10day_confirmation", 
            raise_if_not_found=False
        )
        
        for project in projects:
            existing = self.env["mail.activity"].search([
                ("res_model", "=", "project.project"),
                ("res_id", "=", project.id),
                ("activity_type_id", "=", activity_type.id if activity_type else False),
            ], limit=1)
            
            if not existing:
                project.activity_schedule(
                    act_type_xmlid="ptt_business_core.activity_type_10day_confirmation",
                    date_deadline=today,
                    summary=f"10-Day Confirmation: {project.name}",
                    note=f"Event in 10 days ({target_date}). Confirm all details with client and vendors.",
                    user_id=project.user_id.id if project.user_id else self.env.user.id,
                )
    
    @api.model
    def _cron_3day_vendor_reminder(self):
        """Create 3-day vendor reminder activities for upcoming events.
        
        Runs daily. Finds event projects with ptt_event_date exactly 3 days from today.
        """
        today = fields.Date.today()
        target_date = today + timedelta(days=3)
        
        projects = self.search([
            ("ptt_event_date", "=", target_date),
        ])
        
        activity_type = self.env.ref(
            "ptt_business_core.activity_type_3day_vendor_reminder", 
            raise_if_not_found=False
        )
        
        for project in projects:
            existing = self.env["mail.activity"].search([
                ("res_model", "=", "project.project"),
                ("res_id", "=", project.id),
                ("activity_type_id", "=", activity_type.id if activity_type else False),
            ], limit=1)
            
            if not existing:
                project.activity_schedule(
                    act_type_xmlid="ptt_business_core.activity_type_3day_vendor_reminder",
                    date_deadline=today,
                    summary=f"3-Day Vendor Reminder: {project.name}",
                    note=f"Event in 3 days ({target_date}). Send final reminders to all vendors.",
                    user_id=project.user_id.id if project.user_id else self.env.user.id,
                )
