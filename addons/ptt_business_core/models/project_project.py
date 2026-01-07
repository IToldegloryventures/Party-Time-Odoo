from odoo import models, fields, api
from datetime import datetime, timedelta


class ProjectProject(models.Model):
    _inherit = "project.project"

    # Link back to source CRM Lead
    x_crm_lead_id = fields.Many2one(
        "crm.lead",
        string="Source Opportunity",
        help="The CRM opportunity this project was created from.",
        index=True,
        ondelete="set null",
    )

    # === VENDOR ASSIGNMENTS (ACTUAL) ===
    x_vendor_assignment_ids = fields.One2many(
        "ptt.project.vendor.assignment",
        "project_id",
        string="Vendor Assignments",
        help="Actual vendor assignments and costs for this project.",
    )
    x_actual_total_vendor_costs = fields.Monetary(
        string="Total Actual Vendor Costs",
        compute="_compute_vendor_totals",
        currency_field="currency_id",
        store=True,
        help="Sum of all actual vendor costs.",
    )
    # Estimated values from CRM (read-only for reference)
    x_estimated_total_vendor_costs = fields.Monetary(
        string="Estimated Vendor Costs (from CRM)",
        related="x_crm_lead_id.x_estimated_total_vendor_costs",
        currency_field="currency_id",
        readonly=True,
        help="Original estimated vendor costs from CRM opportunity.",
    )
    x_estimated_client_total = fields.Monetary(
        string="Estimated Client Total (from CRM)",
        related="x_crm_lead_id.x_estimated_client_total",
        currency_field="currency_id",
        readonly=True,
        help="Original estimated client total from CRM opportunity.",
    )
    x_estimated_margin = fields.Monetary(
        string="Estimated Margin (from CRM)",
        related="x_crm_lead_id.x_estimated_margin",
        currency_field="currency_id",
        readonly=True,
        help="Original estimated margin from CRM opportunity.",
    )
    x_estimated_margin_percent = fields.Float(
        string="Estimated Margin % (from CRM)",
        related="x_crm_lead_id.x_estimated_margin_percent",
        readonly=True,
        digits=(16, 2),
        help="Original estimated margin percentage from CRM opportunity.",
    )
    # Actual values
    x_actual_client_total = fields.Monetary(
        string="Actual Client Total",
        currency_field="currency_id",
        help="Total amount client actually pays.",
    )
    x_actual_margin = fields.Monetary(
        string="Actual Margin",
        compute="_compute_vendor_totals",
        currency_field="currency_id",
        store=True,
        help="Actual margin = Client Total - Vendor Costs.",
    )
    x_actual_margin_percent = fields.Float(
        string="Actual Margin %",
        compute="_compute_vendor_totals",
        store=True,
        help="Actual margin percentage.",
    )

    @api.depends("x_vendor_assignment_ids.actual_cost", "x_actual_client_total")
    def _compute_vendor_totals(self):
        """Compute actual vendor costs, margin, and margin percentage."""
        for project in self:
            total_vendor_costs = sum(project.x_vendor_assignment_ids.mapped("actual_cost"))
            project.x_actual_total_vendor_costs = total_vendor_costs
            project.x_actual_margin = project.x_actual_client_total - total_vendor_costs
            if project.x_actual_client_total > 0:
                project.x_actual_margin_percent = (project.x_actual_margin / project.x_actual_client_total) * 100
            else:
                project.x_actual_margin_percent = 0.0

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to auto-create event tasks and set initial stage for event projects."""
        projects = super().create(vals_list)
        for project in projects:
            # Only create tasks if this is an event project (has CRM lead)
            if project.x_crm_lead_id:
                project._set_initial_project_stage()
                project._create_event_tasks()
        return projects

    # Core event identity
    x_event_id = fields.Char(string="Event ID")
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
        help="Copied from the related opportunity / lead.",
    )
    x_event_name = fields.Char(string="Event Name")
    x_event_date = fields.Date(string="Event Date")
    x_event_time = fields.Char(string="Event Time")
    x_guest_count = fields.Integer(string="Guest Count")
    x_venue_name = fields.Char(string="Venue")

    # Schedule
    x_setup_start_time = fields.Char(string="Setup Start Time")
    x_event_start_time = fields.Char(string="Event Start Time")
    x_event_end_time = fields.Char(string="Event End Time")
    x_total_hours = fields.Float(string="Total Hours")
    x_teardown_deadline = fields.Char(string="Tear-Down Deadline")

    # Event details
    x_theme_dress_code = fields.Text(string="Theme, Dress Code, or Style Preference")
    x_special_requirements_desc = fields.Text(string="Special Requirements")
    x_inclement_weather_plan = fields.Text(string="Inclement Weather Plan")
    x_parking_restrictions_desc = fields.Text(string="Parking/Delivery Restrictions")

    def _set_initial_project_stage(self):
        """Set initial project stage based on event date and current date."""
        self.ensure_one()
        if not self.x_event_date:
            return
        
        # Get the Planning stage (default for new projects)
        planning_stage = self.env.ref("ptt_business_core.project_stage_planning", raise_if_not_found=False)
        if planning_stage:
            self.stage_id = planning_stage.id
    
    def _create_event_tasks(self):
        """Auto-create comprehensive event planning tasks and sub-tasks for event projects.
        
        Creates tasks organized by event phase:
        - Booking Confirmation
        - Planning & Coordination
        - Vendor Management
        - Setup & Logistics
        - Event Day Execution
        - Teardown & Follow-up
        """
        self.ensure_one()
        if not self.x_crm_lead_id:
            return  # Only for event projects

        # Get assigned users from CRM Lead's salesperson
        assigned_users = (
            [(6, 0, [self.x_crm_lead_id.user_id.id])]
            if self.x_crm_lead_id.user_id
            else []
        )

        # Get task types (use the new event-specific types)
        todo_type = self.env.ref("ptt_business_core.task_type_todo", raise_if_not_found=False)
        if not todo_type:
            todo_type = self._get_or_create_task_stage("To Do")
        
        # Task 1: Confirm Booking with Client
        booking_task = self.env["project.task"].create({
            "name": "Confirm Booking with Client",
            "project_id": self.id,
            "stage_id": todo_type.id,
            "user_ids": assigned_users,
            "description": "Verify contract signed and retainer received",
        })
        
        # Booking sub-tasks
        booking_subtasks = [
            "Verify Retainer has been paid. Verify remaining balance owed.",
            "Send confirmation email stating contract signed + retainer received",
            "Reiterate event date, venue, time, and agreed services",
        ]
        
        for sub_task_name in booking_subtasks:
            self.env["project.task"].create({
                "name": sub_task_name,
                "project_id": self.id,
                "parent_id": booking_task.id,
                "stage_id": todo_type.id,
                "user_ids": assigned_users,
            })
        
        # Task 2: Planning & Coordination
        planning_task = self.env["project.task"].create({
            "name": "Event Planning & Coordination",
            "project_id": self.id,
            "stage_id": todo_type.id,
            "user_ids": assigned_users,
            "description": "Coordinate all event details and logistics",
        })
        
        planning_subtasks = [
            "Finalize event timeline and schedule",
            "Confirm vendor assignments and contracts",
            "Coordinate with venue (if applicable)",
            "Prepare event day checklist",
            "Confirm guest count and special requirements",
        ]
        
        for sub_task_name in planning_subtasks:
            self.env["project.task"].create({
                "name": sub_task_name,
                "project_id": self.id,
                "parent_id": planning_task.id,
                "stage_id": todo_type.id,
                "user_ids": assigned_users,
            })
        
        # Task 3: Vendor Management
        vendor_task = self.env["project.task"].create({
            "name": "Vendor Management & Coordination",
            "project_id": self.id,
            "stage_id": todo_type.id,
            "user_ids": assigned_users,
            "description": "Manage all vendor assignments and confirmations",
        })
        
        vendor_subtasks = [
            "Confirm all vendor assignments",
            "Verify vendor contracts and pricing",
            "Coordinate vendor delivery/setup times",
            "Confirm vendor contact information",
        ]
        
        for sub_task_name in vendor_subtasks:
            self.env["project.task"].create({
                "name": sub_task_name,
                "project_id": self.id,
                "parent_id": vendor_task.id,
                "stage_id": todo_type.id,
                "user_ids": assigned_users,
            })
        
        # Task 4: Setup & Logistics (only if event date is set)
        if self.x_event_date:
            setup_task = self.env["project.task"].create({
                "name": "Setup & Logistics",
                "project_id": self.id,
                "stage_id": todo_type.id,
                "user_ids": assigned_users,
                "date_deadline": self.x_event_date,  # Due on event date
                "description": "Equipment delivery and setup coordination",
            })
            
            setup_subtasks = [
                "Confirm equipment delivery schedule",
                "Coordinate setup crew assignments",
                "Verify all equipment is available and in good condition",
                "Prepare setup checklist",
            ]
            
            for sub_task_name in setup_subtasks:
                self.env["project.task"].create({
                    "name": sub_task_name,
                    "project_id": self.id,
                    "parent_id": setup_task.id,
                    "stage_id": todo_type.id,
                    "user_ids": assigned_users,
                })
        
        # Task 5: Event Day Execution
        if self.x_event_date:
            event_day_task = self.env["project.task"].create({
                "name": "Event Day Execution",
                "project_id": self.id,
                "stage_id": todo_type.id,
                "user_ids": assigned_users,
                "date_deadline": self.x_event_date,
                "description": "On-site event management and coordination",
            })
            
            event_day_subtasks = [
                "Arrive on-site for final setup check",
                "Coordinate with all vendors on-site",
                "Manage event timeline and flow",
                "Handle any issues or special requests",
                "Ensure guest satisfaction",
            ]
            
            for sub_task_name in event_day_subtasks:
                self.env["project.task"].create({
                    "name": sub_task_name,
                    "project_id": self.id,
                    "parent_id": event_day_task.id,
                    "stage_id": todo_type.id,
                    "user_ids": assigned_users,
                })
        
        # Task 6: Teardown & Follow-up
        if self.x_event_date:
            # Teardown typically happens day after event
            # x_event_date is a Date field, so it's already a date object
            teardown_date = self.x_event_date + timedelta(days=1) if self.x_event_date else None
            teardown_task = self.env["project.task"].create({
                "name": "Teardown & Follow-up",
                "project_id": self.id,
                "stage_id": todo_type.id,
                "user_ids": assigned_users,
                "date_deadline": teardown_date,
                "description": "Equipment removal and post-event follow-up",
            })
            
            teardown_subtasks = [
                "Coordinate equipment teardown and removal",
                "Verify all equipment is returned and accounted for",
                "Send thank you email to client",
                "Request client feedback and testimonials",
                "Update project with final costs and margin",
            ]
            
            for sub_task_name in teardown_subtasks:
                self.env["project.task"].create({
                    "name": sub_task_name,
                    "project_id": self.id,
                    "parent_id": teardown_task.id,
                    "stage_id": todo_type.id,
                    "user_ids": assigned_users,
                })

    def _get_or_create_task_stage(self, stage_name):
        """Get or create a task stage for the project.
        
        This is a fallback method if the XML-defined task types are not found.
        """
        # Search for existing stage linked to this project
        stage = self.env["project.task.type"].search([
            ("name", "=", stage_name),
            ("project_ids", "in", [self.id]),
        ], limit=1)
        
        if not stage:
            # Search for any stage with this name (might exist globally)
            stage = self.env["project.task.type"].search([
                ("name", "=", stage_name),
            ], limit=1)
            
            if not stage:
                # Create new stage if it doesn't exist
                stage = self.env["project.task.type"].create({
                    "name": stage_name,
                    "project_ids": [(4, self.id)],
                })
            else:
                # Link existing stage to this project
                stage.write({"project_ids": [(4, self.id)]})
        else:
            # Ensure project is linked (in case it wasn't)
            if self.id not in stage.project_ids.ids:
                stage.write({"project_ids": [(4, self.id)]})
        
        return stage
    
    @api.depends("x_event_date")
    def _compute_project_stage_from_date(self):
        """Auto-update project stage based on event date.
        
        This method can be called manually or via scheduled action to update
        project stages based on event timeline.
        """
        today = fields.Date.today()
        for project in self:
            if not project.x_event_date:
                continue
            
            event_date = project.x_event_date
            days_until_event = (event_date - today).days
            
            # Get project stages
            planning_stage = self.env.ref("ptt_business_core.project_stage_planning", raise_if_not_found=False)
            setup_stage = self.env.ref("ptt_business_core.project_stage_setup", raise_if_not_found=False)
            event_day_stage = self.env.ref("ptt_business_core.project_stage_event_day", raise_if_not_found=False)
            teardown_stage = self.env.ref("ptt_business_core.project_stage_teardown", raise_if_not_found=False)
            completed_stage = self.env.ref("ptt_business_core.project_stage_completed", raise_if_not_found=False)
            
            # Auto-assign stage based on timeline
            if days_until_event < 0:
                # Event is in the past
                if days_until_event >= -1:
                    # Event was yesterday or today - might be in teardown
                    if teardown_stage:
                        project.stage_id = teardown_stage.id
                else:
                    # Event was more than 1 day ago - should be completed
                    if completed_stage:
                        project.stage_id = completed_stage.id
            elif days_until_event == 0:
                # Event is today
                if event_day_stage:
                    project.stage_id = event_day_stage.id
            elif days_until_event <= 3:
                # Event is within 3 days - setup phase
                if setup_stage:
                    project.stage_id = setup_stage.id
            else:
                # Event is more than 3 days away - planning phase
                if planning_stage:
                    project.stage_id = planning_stage.id

    def action_view_crm_lead(self):
        """Open the source CRM opportunity."""
        self.ensure_one()
        if not self.x_crm_lead_id:
            return False
        return {
            "type": "ir.actions.act_window",
            "name": "Source Opportunity",
            "res_model": "crm.lead",
            "res_id": self.x_crm_lead_id.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_view_tasks(self):
        """Open project tasks."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Project Tasks",
            "res_model": "project.task",
            "view_mode": "list,form,kanban",
            "domain": [("project_id", "=", self.id)],
            "context": {
                "default_project_id": self.id,
                "search_default_project_id": self.id,
            },
        }

    # === SCHEDULED ACTIONS (CRON) ===
    
    @api.model
    def _cron_10day_event_reminder(self):
        """Create 10-day reminder activities for upcoming events.
        
        Runs daily. Finds event projects with x_event_date exactly 10 days from today
        and creates reminder activities for the project manager.
        """
        today = fields.Date.today()
        target_date = today + timedelta(days=10)
        
        # Find projects with events 10 days out
        projects = self.search([
            ("x_event_date", "=", target_date),
            ("x_crm_lead_id", "!=", False),  # Only event projects
        ])
        
        # Get the 10-day confirmation activity type
        activity_type = self.env.ref(
            "ptt_business_core.activity_type_10day_confirmation", 
            raise_if_not_found=False
        )
        
        for project in projects:
            # Check if activity already exists
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
        
        Runs daily. Finds event projects with x_event_date exactly 3 days from today
        and creates reminder activities for vendor follow-up.
        """
        today = fields.Date.today()
        target_date = today + timedelta(days=3)
        
        # Find projects with events 3 days out
        projects = self.search([
            ("x_event_date", "=", target_date),
            ("x_crm_lead_id", "!=", False),  # Only event projects
        ])
        
        # Get the 3-day vendor reminder activity type
        activity_type = self.env.ref(
            "ptt_business_core.activity_type_3day_vendor_reminder", 
            raise_if_not_found=False
        )
        
        for project in projects:
            # Check if activity already exists
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