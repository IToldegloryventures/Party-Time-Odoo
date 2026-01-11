from odoo import models, fields, api
from datetime import timedelta


class ProjectProject(models.Model):
    """Extend project.project for PTT event management.
    
    NOTE: Use standard Odoo fields where possible:
    - user_id = Project Manager / Sales Rep (standard)
    - partner_id = Client (standard)
    - name = Project/Event Name (standard)
    - sale_order_id = Related Sale Order (from sale_project)
    
    Custom PTT fields are for event-specific data only.
    """
    _inherit = "project.project"

    # === VENDOR ASSIGNMENTS (Custom PTT Feature) ===
    x_vendor_assignment_ids = fields.One2many(
        "ptt.project.vendor.assignment",
        "project_id",
        string="Vendor Assignments",
        help="Vendor assignments for this project/event.",
    )

    # === EVENT IDENTITY ===
    x_event_id = fields.Char(
        string="Event Number",
        copy=False,
        index=True,
        help="Unique event identifier for tracking.",
    )
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
        help="Type of event for categorization and reporting.",
    )

    # === EVENT SCHEDULE ===
    x_event_date = fields.Date(
        string="Event Date",
        index=True,
        help="Scheduled event date.",
    )
    x_event_time = fields.Char(string="Event Time")
    x_guest_count = fields.Integer(string="Guest Count")
    x_venue_name = fields.Char(string="Venue")
    x_setup_start_time = fields.Char(string="Setup Start Time")
    x_event_start_time = fields.Char(string="Event Start Time")
    x_event_end_time = fields.Char(string="Event End Time")
    x_total_hours = fields.Float(string="Total Hours")
    x_teardown_deadline = fields.Char(string="Tear-Down Deadline")

    # === EVENT DETAILS ===
    x_theme_dress_code = fields.Text(string="Theme, Dress Code, or Style Preference")
    x_special_requirements_desc = fields.Text(string="Special Requirements")
    x_inclement_weather_plan = fields.Text(string="Inclement Weather Plan")
    x_parking_restrictions_desc = fields.Text(string="Parking/Delivery Restrictions")

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
        if self.x_event_date:
            post_event_deadline = self.x_event_date + timedelta(days=1)
        
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
        
        Runs daily. Finds event projects with x_event_date exactly 10 days from today.
        """
        today = fields.Date.today()
        target_date = today + timedelta(days=10)
        
        projects = self.search([
            ("x_event_date", "=", target_date),
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
        
        Runs daily. Finds event projects with x_event_date exactly 3 days from today.
        """
        today = fields.Date.today()
        target_date = today + timedelta(days=3)
        
        projects = self.search([
            ("x_event_date", "=", target_date),
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
