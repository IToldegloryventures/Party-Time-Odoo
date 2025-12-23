from odoo import models, fields, api


class ProjectProject(models.Model):
    _inherit = "project.project"

    # Link back to source CRM Lead
    x_crm_lead_id = fields.Many2one(
        "crm.lead",
        string="Source Opportunity",
        help="The CRM opportunity this project was created from.",
        index=True,
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
        """Override create to auto-create event tasks for event projects."""
        projects = super().create(vals_list)
        for project in projects:
            # Only create tasks if this is an event project (has CRM lead)
            if project.x_crm_lead_id:
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

    def _create_event_tasks(self):
        """Auto-create event planning tasks and sub-tasks for event projects."""
        self.ensure_one()
        if not self.x_crm_lead_id:
            return  # Only for event projects

        # Get assigned users from CRM Lead's salesperson (Odoo 19 uses user_ids Many2many)
        assigned_users = (
            [(6, 0, [self.x_crm_lead_id.user_id.id])]
            if self.x_crm_lead_id.user_id
            else []
        )

        # Get or create task stages (using task type/stage system)
        # For now, we'll use the default project task stages or create if needed
        # Stage: Follow Up
        follow_up_stage = self._get_or_create_task_stage("Follow Up")
        
        # Create main task: "Confirm Booking with Client"
        main_task = self.env["project.task"].create({
            "name": "Confirm Booking with Client",
            "project_id": self.id,
            "stage_id": follow_up_stage.id,
            "user_ids": assigned_users,
        })
        
        # Create sub-tasks
        sub_tasks_data = [
            "Verify Retainer has been paid. Verify remaining balance owed.",
            "Send confirmation email stating contract signed + retainer received",
            "Reiterate event date, venue, time, and agreed services",
        ]
        
        for sub_task_name in sub_tasks_data:
            self.env["project.task"].create({
                "name": sub_task_name,
                "project_id": self.id,
                "parent_id": main_task.id,
                "stage_id": follow_up_stage.id,
                "user_ids": assigned_users,
            })

    def _get_or_create_task_stage(self, stage_name):
        """Get or create a task stage for the project."""
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

