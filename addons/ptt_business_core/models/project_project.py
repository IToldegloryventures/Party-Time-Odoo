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
    
    # Related field for Sales Rep from CRM (for display in project header)
    x_sales_rep_id = fields.Many2one(
        "res.users",
        string="Sales Rep",
        related="x_crm_lead_id.user_id",
        readonly=True,
        help="Sales representative from the source CRM opportunity.",
    )

    # === VENDOR ASSIGNMENTS ===
    x_vendor_assignment_ids = fields.One2many(
        "ptt.project.vendor.assignment",
        "project_id",
        string="Vendor Assignments",
        help="Vendor assignments for this project.",
    )

    # NOTE: Project creation is handled manually in Odoo.
    # No automatic project creation or task creation from code.
    # The action_create_event_tasks() method below can be called manually via button if needed.
    
    def action_create_event_tasks(self):
        """Button action to create event tasks for this project.
        
        This can be called manually from a button on the project form.
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

    # Core event identity
    x_event_id = fields.Char(string="Event Number")
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
        help="Copied from the related opportunity / lead.",
    )
    x_event_name = fields.Char(string="Event Name")
    x_event_date = fields.Date(string="Scheduled Date", index=True)
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

    # === PROJECT HEADER COMPUTED FIELDS ===
    x_days_until_event = fields.Integer(
        string="Days Until Event",
        compute="_compute_days_until_event",
        store=False,
        help="Number of days until the event date. Negative if event has passed.",
    )
    x_contract_status = fields.Char(
        string="Contract Status",
        compute="_compute_contract_status",
        store=False,
        help="Contract status from related Sales Order.",
    )

    @api.depends("x_event_date")
    def _compute_days_until_event(self):
        """Calculate days until event date."""
        today = fields.Date.today()
        for project in self:
            if project.x_event_date:
                delta = project.x_event_date - today
                project.x_days_until_event = delta.days
            else:
                project.x_days_until_event = 0

    @api.depends("x_crm_lead_id", "x_crm_lead_id.order_ids", "x_crm_lead_id.order_ids.x_contract_status")
    def _compute_contract_status(self):
        """Get contract status from related Sales Order via CRM Lead."""
        for project in self:
            contract_status = "Not Available"
            if project.x_crm_lead_id and project.x_crm_lead_id.order_ids:
                confirmed_orders = project.x_crm_lead_id.order_ids.filtered(lambda so: so.state == 'sale')
                if confirmed_orders:
                    so = confirmed_orders.sorted('create_date', reverse=True)[0]
                    if so.x_contract_status:
                        status_map = {
                            "not_sent": "Not Sent",
                            "sent": "Sent for Signature",
                            "signed": "Signed",
                        }
                        contract_status = status_map.get(so.x_contract_status, so.x_contract_status)
                elif project.x_crm_lead_id.order_ids:
                    so = project.x_crm_lead_id.order_ids[0]
                    if so.x_contract_status:
                        status_map = {
                            "not_sent": "Not Sent",
                            "sent": "Sent for Signature",
                            "signed": "Signed",
                        }
                        contract_status = status_map.get(so.x_contract_status, so.x_contract_status)
            project.x_contract_status = contract_status


    def _set_initial_project_stage(self):
        """Set initial project stage to 'To Do' for new event projects.
        
        Uses sudo() to bypass record rules when accessing project.project.stage.
        """
        self.ensure_one()
        
        todo_stage = self.env.ref("ptt_business_core.project_stage_todo", raise_if_not_found=False)
        if not todo_stage:
            todo_stage = self.env["project.project.stage"].sudo().search(
                [("name", "=", "To Do")], limit=1
            )
        if todo_stage:
            self.sudo().write({"stage_id": todo_stage.id})
    
    def _create_event_tasks(self):
        """Auto-create comprehensive event planning tasks and sub-tasks for event projects.
        
        Creates 9 standard event tasks that apply to all events:
        1. Confirm Booking with Client
        2. Collect Tier-3 Fulfillment Details
        3. Review Client Deliverables Checklist
        4. Coordinate Vendor Assignments
        5. Vendor Brief & Confirmation
        6. Prepare Event Resources & Logistics
        7. Client Communications & Check-Ins
        8. Final Payment Check & Invoice Follow-up
        9. Post-Event Closure / Review
        
        Note: Uses sudo() for task creation to bypass record rules on project.task.type
        since this is an automated system process triggered by Sales Order confirmation.
        """
        self.ensure_one()
        if not self.x_crm_lead_id:
            return  # Only for event projects

        assigned_users = (
            [(6, 0, [self.x_crm_lead_id.user_id.id])]
            if self.x_crm_lead_id.user_id
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
        
        booking_subtasks = [
            "Verify Retainer has been paid. Verify remaining balance owed.",
            "Send confirmation email stating contract signed + retainer received",
            "Reiterate event date, venue, time, and agreed services",
        ]
        
        for sub_task_name in booking_subtasks:
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
        
        tier3_subtasks = [
            "Venue access info (load-in times, restrictions, contacts)",
            "Rider / Equipment Setup specifications",
            "Vendor needs, power, staging, logistics",
            "Special requests (e.g. backup, transportation)",
        ]
        
        for sub_task_name in tier3_subtasks:
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
        
        deliverables_subtasks = [
            "Song selections (first dance, special requests)",
            "Timeline (ceremony, reception, breaks)",
            "Venue logistics (floor plan, layout)",
            "Contact point on event day",
            "Guest count confirmation",
        ]
        
        for sub_task_name in deliverables_subtasks:
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
            "description": "Assign internal vendors to event and provide task lists",
        })
        
        vendor_assign_subtasks = [
            "Assign internal vendor(s) to event",
            "Provide vendors with relevant task list, rider info, schedule",
            "Confirm vendors' availability, rates, and contracts",
        ]
        
        for sub_task_name in vendor_assign_subtasks:
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
        
        vendor_brief_subtasks = [
            "Confirm vendor requirements for equipment, load-in, contact person",
            "Confirm required documents (COI, contract, tax info)",
            "Confirm vendor acceptance",
        ]
        
        for sub_task_name in vendor_brief_subtasks:
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
        
        resources_subtasks = [
            "Inventory / equipment prep",
            "Transport / loading plan",
            "Backup gear / redundancy checks",
            "Power & staging setup plan",
        ]
        
        for sub_task_name in resources_subtasks:
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
        
        communications_subtasks = [
            "Execute appropriate check-ins",
            "Confirm all logistics 1-2 weeks prior",
            "Issue reminders for outstanding client tasks (song lists, special requests)",
        ]
        
        for sub_task_name in communications_subtasks:
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
        
        payment_subtasks = [
            "Review invoice balance and confirm full payment status",
            "Flag and follow up on unpaid balances",
            "Update system status to \"Final Payment Received\"",
        ]
        
        for sub_task_name in payment_subtasks:
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
        
        post_event_subtasks = [
            "Confirm event ended as scheduled",
            "Gather client feedback / survey link",
            "Document lessons learned or special notes for future events",
        ]
        
        for sub_task_name in post_event_subtasks:
            Task.create({
                "name": sub_task_name,
                "project_id": self.id,
                "parent_id": post_event_task.id,
                "stage_id": todo_type.id,
                "user_ids": assigned_users,
            })

    def _get_or_create_task_stage(self, stage_name):
        """Get or create a task stage for the project.
        
        This is a fallback method if the XML-defined task types are not found.
        """
        stage = self.env["project.task.type"].search([
            ("name", "=", stage_name),
            ("project_ids", "in", [self.id]),
        ], limit=1)
        
        if not stage:
            stage = self.env["project.task.type"].search([
                ("name", "=", stage_name),
            ], limit=1)
            
            if not stage:
                stage = self.env["project.task.type"].create({
                    "name": stage_name,
                    "project_ids": [(4, self.id)],
                })
            else:
                stage.write({"project_ids": [(4, self.id)]})
        else:
            if self.id not in stage.project_ids.ids:
                stage.write({"project_ids": [(4, self.id)]})
        
        return stage
    

    x_sale_order_count = fields.Integer(
        string="# Sales Orders",
        compute="_compute_sale_order_count",
        help="Number of Sales Orders from the source CRM opportunity",
    )
    
    @api.depends("x_crm_lead_id", "x_crm_lead_id.order_ids")
    def _compute_sale_order_count(self):
        for project in self:
            if project.x_crm_lead_id:
                project.x_sale_order_count = len(project.x_crm_lead_id.order_ids)
            else:
                project.x_sale_order_count = 0
    
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
    
    def action_view_sale_orders(self):
        """Open Sales Orders from the source CRM opportunity."""
        self.ensure_one()
        if not self.x_crm_lead_id or not self.x_crm_lead_id.order_ids:
            return False
        return {
            "type": "ir.actions.act_window",
            "name": "Sales Orders",
            "res_model": "sale.order",
            "view_mode": "tree,form",
            "domain": [("id", "in", self.x_crm_lead_id.order_ids.ids)],
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
        
        projects = self.search([
            ("x_event_date", "=", target_date),
            ("x_crm_lead_id", "!=", False),
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
        
        Runs daily. Finds event projects with x_event_date exactly 3 days from today
        and creates reminder activities for vendor follow-up.
        """
        today = fields.Date.today()
        target_date = today + timedelta(days=3)
        
        projects = self.search([
            ("x_event_date", "=", target_date),
            ("x_crm_lead_id", "!=", False),
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
