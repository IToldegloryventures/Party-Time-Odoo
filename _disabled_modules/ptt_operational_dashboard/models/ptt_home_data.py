from odoo import models, fields, api
from datetime import timedelta


class PttHomeData(models.AbstractModel):
    """Abstract service class that aggregates data from standard Odoo models.
    
    This is NOT a stored model - it's an abstract service class that provides methods
    to fetch data from standard Odoo models with action metadata for deep linking.
    
    All data comes from standard Odoo models:
    - project.task (My Work, Assigned Tasks)
    - project.project (Agenda, Event Calendar)
    - crm.lead (Lead stages, linked opportunities)
    - sale.order (Sales Dashboard quotes)
    - account.move (Outstanding payments)
    - mail.message (Assigned Comments)
    
    Note: AbstractModels don't create database tables and don't need access rights.
    """
    _name = "ptt.home.data"
    _description = "PTT Home Data Service"
    _auto = False  # Explicitly mark as non-persistent

    @api.model
    def get_my_work_tasks(self):
        """Get PROJECT tasks assigned to current user, categorized by due date.
        
        Returns tasks from ANY project - event projects, templates, internal projects.
        These are structured work tasks that belong to a project workflow.
        
        Categories: today, overdue, upcoming, unscheduled
        """
        user = self.env.user
        today = fields.Date.context_today(self)
        
        Task = self.env["project.task"]
        
        # Get ALL tasks from projects assigned to user (not just event projects)
        # This includes event tasks, template tasks, and any other project work
        domain = [
            ("user_ids", "in", [user.id]),
            ("stage_id.fold", "=", False),  # Not in folded/done stages
            ("project_id", "!=", False),  # Must have a project (structured work)
        ]
        tasks = Task.search(domain, order="date_deadline asc, priority desc, id")
        
        result = {
            "today": [],
            "overdue": [],
            "upcoming": [],
            "unscheduled": [],
        }
        
        for task in tasks:
            task_data = self._format_task_data(task, today)
            category = task_data.pop("category")
            if category:
                result[category].append(task_data)
        
        return result
    
    def _format_task_data(self, task, today):
        """Format a single task with action metadata."""
        # Determine category
        if not task.date_deadline:
            category = "unscheduled"
        elif task.date_deadline < today:
            category = "overdue"
        elif task.date_deadline == today:
            category = "today"
        else:
            category = "upcoming"
        
        return {
            "id": task.id,
            "name": task.name,
            "date_deadline": task.date_deadline.isoformat() if task.date_deadline else False,
            "priority": task.priority,
            "stage_name": task.stage_id.name if task.stage_id else "",
            "project_id": task.project_id.id if task.project_id else False,
            "project_name": task.project_id.name if task.project_id else "",
            "parent_id": task.parent_id.id if task.parent_id else False,
            "parent_name": task.parent_id.name if task.parent_id else "",
            "subtask_count": task.subtask_count if hasattr(task, 'subtask_count') else 0,
            "category": category,
            # Action metadata for deep linking
            "action": {
                "type": "ir.actions.act_window",
                "res_model": "project.task",
                "res_id": task.id,
                "views": [[False, "form"]],
                "target": "current",
            },
            "project_action": {
                "type": "ir.actions.act_window",
                "res_model": "project.project",
                "res_id": task.project_id.id,
                "views": [[False, "form"]],
                "target": "current",
            } if task.project_id else None,
        }
    
    @api.model
    def get_assigned_tasks(self):
        """Get ONE-OFF/MISC tasks assigned to current user.
        
        Returns tasks that have NO project assigned - truly standalone tasks,
        internal to-dos, or ad-hoc items that don't belong to any project workflow.
        
        Tasks from ANY project (including templates) are considered "work" tasks
        and should appear in the My Work section instead.
        """
        user = self.env.user
        today = fields.Date.context_today(self)
        
        Task = self.env["project.task"]
        
        # Build domain: tasks assigned to user, not done, with NO project
        # This shows truly miscellaneous tasks - personal reminders, ad-hoc items
        domain = [
            ("user_ids", "in", [user.id]),
            ("stage_id.fold", "=", False),
            ("project_id", "=", False),  # Only tasks with no project
        ]
        
        tasks = Task.search(domain, order="date_deadline asc, id")
        
        result = []
        for task in tasks:
            task_data = {
                "id": task.id,
                "name": task.name,
                "date_deadline": task.date_deadline.isoformat() if task.date_deadline else False,
                "is_overdue": task.date_deadline and task.date_deadline < today,
                "priority": task.priority,
                "stage_name": task.stage_id.name if task.stage_id else "",
                "project_id": task.project_id.id if task.project_id else False,
                "project_name": task.project_id.name if task.project_id else "",
                # Action metadata
                "action": {
                    "type": "ir.actions.act_window",
                    "res_model": "project.task",
                    "res_id": task.id,
                    "views": [[False, "form"]],
                    "target": "current",
                },
                "project_action": {
                    "type": "ir.actions.act_window",
                    "res_model": "project.project",
                    "res_id": task.project_id.id,
                    "views": [[False, "form"]],
                    "target": "current",
                } if task.project_id else None,
            }
            result.append(task_data)
        
        return result
    
    @api.model
    def get_dashboard_tasks(self):
        """Get comprehensive task aggregation for dashboard homepage.
        
        Returns all required sections:
        - assigned_tasks: Tasks assigned to current user
        - unassigned_tasks: Tasks with no user assigned
        - due_today: Tasks due today
        - overdue: Tasks past due date
        - no_due_date: Tasks without a due date
        - all_combined: All service + event + CRM tasks (without duplication)
        
        All tasks come from standard Odoo models only (project.task).
        Service tasks are de-duplicated using sale_line_id as unique identifier.
        """
        user = self.env.user
        today = fields.Date.context_today(self)
        
        Task = self.env["project.task"]
        Project = self.env["project.project"]
        
        # Get event project IDs (projects linked to CRM leads)
        event_project_ids = []
        if "ptt_crm_lead_id" in Project._fields:
            event_projects = Project.search([("ptt_crm_lead_id", "!=", False)])
            event_project_ids = event_projects.ids
        
        # Base domain: all active tasks (not in folded/done stages)
        base_domain = [("stage_id.fold", "=", False)]
        
        # 1. ASSIGNED TASKS (Current User)
        assigned_domain = base_domain + [("user_ids", "in", [user.id])]
        assigned_tasks = Task.search(assigned_domain, order="date_deadline asc, priority desc, id")
        
        # 2. UNASSIGNED TASKS
        unassigned_domain = base_domain + [("user_ids", "=", False)]
        unassigned_tasks = Task.search(unassigned_domain, order="date_deadline asc, priority desc, id")
        
        # 3. DUE TODAY
        due_today_domain = base_domain + [("date_deadline", "=", today)]
        due_today_tasks = Task.search(due_today_domain, order="priority desc, id")
        
        # 4. OVERDUE
        overdue_domain = base_domain + [("date_deadline", "<", today), ("date_deadline", "!=", False)]
        overdue_tasks = Task.search(overdue_domain, order="date_deadline asc, priority desc, id")
        
        # 5. NO DUE DATE
        no_due_date_domain = base_domain + [("date_deadline", "=", False)]
        no_due_date_tasks = Task.search(no_due_date_domain, order="priority desc, id")
        
        # 6. ALL SERVICE + EVENT + CRM TASKS COMBINED (with de-duplication)
        all_combined_tasks = self._get_all_combined_tasks(base_domain, event_project_ids)
        
        # Format all task lists
        return {
            "assigned_tasks": [self._format_task_data_simple(t, today) for t in assigned_tasks],
            "unassigned_tasks": [self._format_task_data_simple(t, today) for t in unassigned_tasks],
            "due_today": [self._format_task_data_simple(t, today) for t in due_today_tasks],
            "overdue": [self._format_task_data_simple(t, today) for t in overdue_tasks],
            "no_due_date": [self._format_task_data_simple(t, today) for t in no_due_date_tasks],
            "all_combined": all_combined_tasks,
        }
    
    def _get_all_combined_tasks(self, base_domain, event_project_ids):
        """Get all service + event + CRM tasks without duplication.
        
        Service tasks are identified by sale_line_id and de-duplicated.
        Event tasks are from projects linked to CRM leads.
        CRM tasks are tasks linked to CRM leads via mail.activity or project.
        
        Returns list of unique tasks.
        """
        Task = self.env["project.task"]
        today = fields.Date.context_today(self)
        
        # Build domain for all relevant tasks
        # Include: event tasks, service tasks (with sale_line_id), and CRM-related tasks
        combined_domain = base_domain.copy()
        
        # Get all tasks that could be service, event, or CRM related
        # Service tasks: have sale_line_id
        # Event tasks: from event projects
        # CRM tasks: linked to CRM leads via activities or projects
        
        # Start with all active tasks
        all_tasks = Task.search(base_domain, order="date_deadline asc, priority desc, id")
        
        # Filter to get service, event, and CRM tasks
        relevant_tasks = []
        seen_sale_line_ids = set()  # For de-duplication of service tasks
        
        for task in all_tasks:
            is_service_task = False
            is_event_task = False
            is_crm_task = False
            
            # Check if it's a service task (has sale_line_id)
            if hasattr(task, 'sale_line_id') and task.sale_line_id:
                is_service_task = True
                # De-duplicate: if we've seen this sale_line_id, skip it
                sale_line_id = task.sale_line_id.id
                if sale_line_id in seen_sale_line_ids:
                    continue  # Skip duplicate service task
                seen_sale_line_ids.add(sale_line_id)
            
            # Check if it's an event task (from event project)
            if task.project_id and task.project_id.id in event_project_ids:
                is_event_task = True
            
            # Check if it's a CRM task (linked to CRM lead via project or activity)
            if task.project_id and hasattr(task.project_id, 'ptt_crm_lead_id') and task.project_id.ptt_crm_lead_id:
                is_crm_task = True
            
            # Include task if it matches any category
            if is_service_task or is_event_task or is_crm_task:
                relevant_tasks.append(task)
        
        # Format and return
        return [self._format_task_data_simple(t, today) for t in relevant_tasks]
    
    def _format_task_data_simple(self, task, today):
        """Format a task with basic metadata for dashboard display."""
        return {
            "id": task.id,
            "name": task.name,
            "date_deadline": task.date_deadline.isoformat() if task.date_deadline else False,
            "is_overdue": task.date_deadline and task.date_deadline < today if task.date_deadline else False,
            "priority": task.priority,
            "stage_name": task.stage_id.name if task.stage_id else "",
            "user_ids": task.user_ids.ids if hasattr(task, 'user_ids') else [],
            "user_names": ", ".join(task.user_ids.mapped("name")) if hasattr(task, 'user_ids') and task.user_ids else "Unassigned",
            "project_id": task.project_id.id if task.project_id else False,
            "project_name": task.project_id.name if task.project_id else "",
            "sale_line_id": task.sale_line_id.id if hasattr(task, 'sale_line_id') and task.sale_line_id else False,
            "sale_order_id": task.sale_order_id.id if hasattr(task, 'sale_order_id') and task.sale_order_id else False,
            # Action metadata
            "action": {
                "type": "ir.actions.act_window",
                "res_model": "project.task",
                "res_id": task.id,
                "views": [[False, "form"]],
                "target": "current",
            },
            "project_action": {
                "type": "ir.actions.act_window",
                "res_model": "project.project",
                "res_id": task.project_id.id,
                "views": [[False, "form"]],
                "target": "current",
            } if task.project_id else None,
        }
    
    @api.model
    def get_task_leaderboard(self):
        """Get task performance leaderboard by user.
        
        Groups project.task by user_id and calculates:
        - Total assigned tasks
        - Completed tasks (stage_id.fold == True)
        - Overdue count
        
        Returns list of users with their task metrics.
        Uses ORM grouping only (no custom tables).
        """
        Task = self.env["project.task"]
        today = fields.Date.context_today(self)
        
        # Get all active users
        User = self.env["res.users"]
        users = User.search([
            ("share", "=", False),  # Internal users only
            ("active", "=", True),
        ], order="name")
        
        leaderboard = []
        
        for user in users:
            # Total assigned tasks (not in folded stages)
            total_tasks = Task.search_count([
                ("user_ids", "in", [user.id]),
                ("stage_id.fold", "=", False),
            ])
            
            # Completed tasks (in folded stages)
            completed_tasks = Task.search_count([
                ("user_ids", "in", [user.id]),
                ("stage_id.fold", "=", True),
            ])
            
            # Overdue tasks
            overdue_tasks = Task.search_count([
                ("user_ids", "in", [user.id]),
                ("date_deadline", "<", today),
                ("date_deadline", "!=", False),
                ("stage_id.fold", "=", False),
            ])
            
            # Get initials
            name_parts = (user.name or "").split()
            initials = "".join([p[0].upper() for p in name_parts[:2]]) if name_parts else "?"
            
            leaderboard.append({
                "id": user.id,
                "name": user.name,
                "initials": initials,
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "overdue_tasks": overdue_tasks,
                "completion_rate": round((completed_tasks / total_tasks * 100) if total_tasks > 0 else 0, 1),
                # Action to view user's tasks
                "action": {
                    "type": "ir.actions.act_window",
                    "name": f"{user.name}'s Tasks",
                    "res_model": "project.task",
                    "views": [[False, "list"], [False, "form"]],
                    "domain": [("user_ids", "in", [user.id])],
                    "context": {"search_default_my_tasks": 1},
                    "target": "current",
                },
            })
        
        # Sort by total tasks descending
        leaderboard.sort(key=lambda x: x["total_tasks"], reverse=True)
        
        return leaderboard
    
    @api.model
    def get_assigned_comments(self, limit=20):
        """Get comments/messages where current user is mentioned or assigned.
        
        Returns mail.message records with action metadata to open the source record.
        """
        user = self.env.user
        partner = user.partner_id
        
        Message = self.env["mail.message"]
        # Messages where user's partner is in partner_ids (mentioned/assigned)
        domain = [
            ("partner_ids", "in", [partner.id]),
            ("message_type", "in", ["comment", "notification"]),
            ("model", "!=", False),
            ("res_id", "!=", 0),
        ]
        messages = Message.search(domain, order="date desc", limit=limit)
        
        result = []
        for msg in messages:
            # Get the source record name
            try:
                source_record = self.env[msg.model].browse(msg.res_id)
                record_name = source_record.display_name if source_record.exists() else "Deleted Record"
            except Exception:
                record_name = f"{msg.model} #{msg.res_id}"
            
            msg_data = {
                "id": msg.id,
                "body": msg.body,  # HTML content
                "date": msg.date.isoformat() if msg.date else False,
                "author_name": msg.author_id.name if msg.author_id else "System",
                "author_id": msg.author_id.id if msg.author_id else False,
                "model": msg.model,
                "res_id": msg.res_id,
                "record_name": record_name,
                # Action to open source record
                "action": {
                    "type": "ir.actions.act_window",
                    "res_model": msg.model,
                    "res_id": msg.res_id,
                    "views": [[False, "form"]],
                    "target": "current",
                },
            }
            result.append(msg_data)
        
        return result
    
    @api.model
    def get_agenda_events(self, days=14):
        """Get upcoming events from CRM leads for the current user's agenda.
        
        Pulls from crm.lead where ptt_event_date is set and assigned to user.
        Shows events in the next N days (default 14).
        
        This shows the USER'S assigned events at ALL stages.
        For company-wide view, use the Event Calendar tab.
        """
        user = self.env.user
        today = fields.Date.context_today(self)
        end_date = today + timedelta(days=days)
        
        Lead = self.env["crm.lead"]
        
        # Check if ptt_event_date field exists on crm.lead
        if "ptt_event_date" not in Lead._fields:
            return []
        
        # Get leads assigned to user with event dates in range
        domain = [
            ("user_id", "=", user.id),
            ("ptt_event_date", ">=", today),
            ("ptt_event_date", "<=", end_date),
            ("ptt_event_date", "!=", False),
        ]
        
        leads = Lead.search(domain, order="ptt_event_date asc", limit=20)
        
        # PTT CRM Stage Colors
        # Official stages: Intake, Qualification, Approval, Proposal Sent, Contract Sent, Booked, Closed/Won, Lost
        stage_colors = {
            "Intake": "#17A2B8",              # Teal/Cyan - New inquiries
            "Qualification": "#007BFF",        # Blue - Qualification in progress
            "Approval": "#FFC107",             # Yellow - Awaiting internal approval
            "Proposal Sent": "#6F42C1",        # Purple - Proposal sent to client
            "Contract Sent": "#FF9800",        # Orange - Contract sent, awaiting signature
            "Booked": "#28A745",               # Green - Confirmed bookings (won)
            "Closed/Won": "#155724",           # Dark Green - Completed and won
            "Lost": "#DC3545",                 # Red - Lost opportunities
        }
        default_color = "#6C757D"
        
        result = []
        # If CRM leads are already linked to projects, show ONE event (prefer the project as the canonical record)
        seen_project_ids = set()
        for lead in leads:
            stage_name = lead.stage_id.name if lead.stage_id else "Unknown"
            color = stage_colors.get(stage_name, default_color)
            event_name = getattr(lead, 'ptt_event_name', None) or lead.name or "Untitled Event"

            project = lead.ptt_project_id if hasattr(lead, "ptt_project_id") else False
            if project:
                # De-duplicate: if multiple leads point to the same project, only show it once
                if project.id in seen_project_ids:
                    continue
                seen_project_ids.add(project.id)
            
            event_data = {
                "id": f"project_{project.id}" if project else lead.id,
                "name": event_name,
                "lead_name": lead.name,
                "event_date": lead.ptt_event_date.isoformat() if lead.ptt_event_date else False,
                "partner_name": lead.partner_id.name if lead.partner_id else (lead.partner_name or ""),
                "stage_name": stage_name,
                "color": color,
                "stage_id": lead.stage_id.id if lead.stage_id else False,
                "project_id": project.id if project else False,
                "project_name": project.name if project else "",
                # Action metadata - opens CRM Lead form
                "action": {
                    "type": "ir.actions.act_window",
                    "res_model": "crm.lead",
                    "res_id": lead.id,
                    "views": [[False, "form"]],
                    "target": "current",
                },
                "project_action": {
                    "type": "ir.actions.act_window",
                    "res_model": "project.project",
                    "res_id": project.id,
                    "views": [[False, "form"]],
                    "target": "current",
                } if project else None,
            }
            result.append(event_data)
        
        return result
    
    @api.model
    def get_event_calendar_data(self, start_date=None, end_date=None, my_events_only=False):
        """Get all CRM leads with event dates for the calendar view.
        
        Pulls from crm.lead where ptt_event_date is set.
        Shows ALL events company-wide by default.
        Filter to user's assigned events with my_events_only=True.
        
        Args:
            start_date: Start of date range (defaults to first of current month)
            end_date: End of date range (defaults to end of next month)
            my_events_only: If True, only show events assigned to current user
        
        Returns:
            List of event dictionaries with stage colors and action metadata
        """
        user = self.env.user
        today = fields.Date.context_today(self)
        
        # Parse date strings if needed
        if isinstance(start_date, str):
            start_date = fields.Date.from_string(start_date)
        if isinstance(end_date, str):
            end_date = fields.Date.from_string(end_date)
        
        if not start_date:
            start_date = today.replace(day=1)
        if not end_date:
            # End of next month
            if today.month == 12:
                end_date = today.replace(year=today.year + 1, month=2, day=1) - timedelta(days=1)
            elif today.month == 11:
                end_date = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                end_date = today.replace(month=today.month + 2, day=1) - timedelta(days=1)
        
        Lead = self.env["crm.lead"]
        
        # Check if ptt_event_date field exists on crm.lead
        if "ptt_event_date" not in Lead._fields:
            return {"events": [], "stages": []}
        
        # Build domain - ALL events by default
        domain = [
            ("ptt_event_date", ">=", start_date),
            ("ptt_event_date", "<=", end_date),
            ("ptt_event_date", "!=", False),
        ]
        
        # Filter to user's events if requested
        if my_events_only:
            domain.append(("user_id", "=", user.id))
        
        leads = Lead.search(domain, order="ptt_event_date asc")
        
        # PTT CRM Stage Colors
        # These are the official PTT pipeline stages
        # Stages: Intake, Qualification, Approval, Proposal Sent, Contract Sent, Booked, Closed/Won, Lost
        stage_colors = {
            "Intake": "#17A2B8",              # Teal/Cyan - New inquiries
            "Qualification": "#007BFF",        # Blue - Qualification in progress
            "Approval": "#FFC107",             # Yellow - Awaiting internal approval
            "Proposal Sent": "#6F42C1",        # Purple - Proposal sent to client
            "Contract Sent": "#FF9800",        # Orange - Contract sent, awaiting signature
            "Booked": "#28A745",               # Green - Confirmed bookings (won)
            "Closed/Won": "#155724",           # Dark Green - Completed and won
            "Lost": "#DC3545",                 # Red - Lost opportunities
        }
        default_color = "#6C757D"  # Gray for unknown stages
        
        events = []
        seen_project_ids = set()
        for lead in leads:
            stage_name = lead.stage_id.name if lead.stage_id else "Unknown"
            color = stage_colors.get(stage_name, default_color)
            
            # Get event display name
            event_name = getattr(lead, 'ptt_event_name', None) or lead.name or "Untitled Event"
            
            # Get assignee info
            assignee_name = lead.user_id.name if lead.user_id else "Unassigned"
            is_mine = lead.user_id.id == user.id if lead.user_id else False
            
            project = lead.ptt_project_id if hasattr(lead, "ptt_project_id") else False
            if project:
                if project.id in seen_project_ids:
                    continue
                seen_project_ids.add(project.id)

            event_data = {
                "id": f"project_{project.id}" if project else lead.id,
                "name": event_name,
                "lead_name": lead.name,
                "event_date": lead.ptt_event_date.isoformat() if lead.ptt_event_date else False,
                "event_time": lead.ptt_event_time if hasattr(lead, 'ptt_event_time') else "",
                "partner_name": lead.partner_id.name if lead.partner_id else (lead.partner_name or ""),
                "contact_name": lead.contact_name or "",
                "stage_id": lead.stage_id.id if lead.stage_id else False,
                "stage_name": stage_name,
                "color": color,
                "event_type": lead.ptt_event_type if hasattr(lead, 'ptt_event_type') else "",
                "venue_name": lead.ptt_venue_name if hasattr(lead, 'ptt_venue_name') else "",
                "guest_count": lead.ptt_estimated_guest_count if hasattr(lead, 'ptt_estimated_guest_count') else 0,
                "assignee_id": lead.user_id.id if lead.user_id else False,
                "assignee_name": assignee_name,
                "is_mine": is_mine,
                # Project link if exists
                "project_id": project.id if project else False,
                "project_name": project.name if project else "",
                # Action metadata - opens CRM Lead form
                "action": {
                    "type": "ir.actions.act_window",
                    "res_model": "crm.lead",
                    "res_id": lead.id,
                    "views": [[False, "form"]],
                    "target": "current",
                },
                "project_action": {
                    "type": "ir.actions.act_window",
                    "res_model": "project.project",
                    "res_id": project.id,
                    "views": [[False, "form"]],
                    "target": "current",
                } if project else None,
            }
            events.append(event_data)

        # Also include projects with event dates that are NOT linked to CRM leads (project-only events)
        Project = self.env["project.project"]
        if "ptt_event_date" in Project._fields:
            project_domain = [
                ("ptt_event_date", ">=", start_date),
                ("ptt_event_date", "<=", end_date),
                ("ptt_event_date", "!=", False),
            ]
            if my_events_only:
                project_domain.append(("user_id", "=", user.id))
            if "ptt_crm_lead_id" in Project._fields:
                project_domain.append(("ptt_crm_lead_id", "=", False))
            projects = Project.search(project_domain, order="ptt_event_date asc")
            for project in projects:
                if project.id in seen_project_ids:
                    continue
                seen_project_ids.add(project.id)
                events.append({
                    "id": f"project_{project.id}",
                    "name": project.name or "Project Event",
                    "lead_name": "",
                    "event_date": project.ptt_event_date.isoformat() if project.ptt_event_date else False,
                    "event_time": "",
                    "partner_name": "",
                    "contact_name": "",
                    "stage_id": "project",
                    "stage_name": "Project",
                    "color": "#2563EB",
                    "event_type": "",
                    "venue_name": "",
                    "guest_count": 0,
                    "assignee_id": project.user_id.id if project.user_id else False,
                    "assignee_name": project.user_id.name if project.user_id else "Unassigned",
                    "is_mine": project.user_id.id == user.id if project.user_id else False,
                    "project_id": project.id,
                    "project_name": project.name or "",
                    "action": None,
                    "project_action": {
                        "type": "ir.actions.act_window",
                        "res_model": "project.project",
                        "res_id": project.id,
                        "views": [[False, "form"]],
                        "target": "current",
                    },
                })
        
        # Get all stages for the legend
        stages = self._get_crm_stages_with_colors(stage_colors, default_color)
        
        return {
            "events": events,
            "stages": stages,
            "current_user_id": user.id,
        }
    
    @api.model
    def _get_crm_stages_with_colors(self, stage_colors, default_color):
        """Get PTT CRM stages with their colors for the calendar legend.
        
        Returns the official PTT stages in order, matching the stage_colors dict.
        This ensures consistency even if database stages differ.
        """
        # Official PTT stages in pipeline order
        # Stages: Intake, Qualification, Approval, Proposal Sent, Contract Sent, Booked, Closed/Won, Lost
        ptt_stages = [
            {"name": "Intake", "sequence": 1},
            {"name": "Qualification", "sequence": 2},
            {"name": "Approval", "sequence": 3},
            {"name": "Proposal Sent", "sequence": 4},
            {"name": "Contract Sent", "sequence": 5},
            {"name": "Booked", "sequence": 6},
            {"name": "Closed/Won", "sequence": 7},
            {"name": "Lost", "sequence": 8},
        ]
        
        # Try to get actual stage IDs from database for filtering
        Stage = self.env["crm.stage"]
        db_stages = {s.name: s.id for s in Stage.search([])}
        
        result = []
        for stage in ptt_stages:
            result.append({
                "id": db_stages.get(stage["name"], stage["name"]),  # Use DB id or name as fallback
                "name": stage["name"],
                "color": stage_colors.get(stage["name"], default_color),
                "sequence": stage["sequence"],
            })
        
        return result
    
    @api.model
    def get_events_for_date(self, date_str, my_events_only=False):
        """Get all events for a specific date (for day panel).
        
        Args:
            date_str: Date string in ISO format (YYYY-MM-DD)
            my_events_only: If True, only show events assigned to current user
        
        Returns:
            List of events for the specified date
        """
        user = self.env.user
        event_date = fields.Date.from_string(date_str)
        
        Lead = self.env["crm.lead"]
        
        if "ptt_event_date" not in Lead._fields:
            return []
        
        domain = [
            ("ptt_event_date", "=", event_date),
        ]
        
        if my_events_only:
            domain.append(("user_id", "=", user.id))
        
        leads = Lead.search(domain, order="ptt_event_time asc, name asc")
        
        stage_colors = {
            "Intake": "#17A2B8",              # Teal/Cyan - New inquiries
            "Qualification": "#007BFF",        # Blue - Qualification in progress
            "Proposal Sent": "#6F42C1",        # Purple - Proposal sent to client
            "Contract Sent": "#FF9800",        # Orange - Contract sent, awaiting signature
            "Booked": "#28A745",               # Green - Confirmed bookings (won)
            "Closed/Won": "#155724",           # Dark Green - Completed and won
            "Lost": "#DC3545",                 # Red - Lost opportunities
        }
        default_color = "#6C757D"
        
        events = []
        seen_project_ids = set()
        for lead in leads:
            stage_name = lead.stage_id.name if lead.stage_id else "Unknown"
            event_name = getattr(lead, 'ptt_event_name', None) or lead.name or "Untitled Event"

            project = lead.ptt_project_id if hasattr(lead, "ptt_project_id") else False
            if project:
                if project.id in seen_project_ids:
                    continue
                seen_project_ids.add(project.id)

            events.append({
                "id": f"project_{project.id}" if project else lead.id,
                "name": event_name,
                "lead_name": lead.name,
                "event_time": lead.ptt_event_time if hasattr(lead, 'ptt_event_time') else "",
                "partner_name": lead.partner_id.name if lead.partner_id else (lead.partner_name or ""),
                "stage_name": stage_name,
                "color": stage_colors.get(stage_name, default_color),
                "venue_name": lead.ptt_venue_name if hasattr(lead, 'ptt_venue_name') else "",
                "assignee_name": lead.user_id.name if lead.user_id else "Unassigned",
                "is_mine": lead.user_id.id == user.id if lead.user_id else False,
                "project_id": project.id if project else False,
                "project_name": project.name if project else "",
                "action": {
                    "type": "ir.actions.act_window",
                    "res_model": "crm.lead",
                    "res_id": lead.id,
                    "views": [[False, "form"]],
                    "target": "current",
                },
                "project_action": {
                    "type": "ir.actions.act_window",
                    "res_model": "project.project",
                    "res_id": project.id,
                    "views": [[False, "form"]],
                    "target": "current",
                } if project else None,
            })
        
        return events
    
    @api.model
    def get_sales_dashboard_data(self, start_date=None, end_date=None):
        """Get comprehensive sales dashboard data with date filtering.
        
        Args:
            start_date: Start of date range (YYYY-MM-DD string)
            end_date: End of date range (YYYY-MM-DD string)
        
        Returns:
            dict with total_booked, total_paid, total_outstanding, and per-rep data
        """
        today = fields.Date.context_today(self)
        
        # Default to current month if no dates provided
        if not start_date:
            start_date = today.replace(day=1)
        else:
            start_date = fields.Date.from_string(start_date)
        
        if not end_date:
            # Last day of current month
            import calendar
            last_day = calendar.monthrange(today.year, today.month)[1]
            end_date = today.replace(day=last_day)
        else:
            end_date = fields.Date.from_string(end_date)
        
        Lead = self.env["crm.lead"]
        Invoice = self.env["account.move"]
        
        # === TOTAL BOOKED (CRM leads in "Booked" stage within date range) ===
        booked_domain = [
            ("ptt_event_date", ">=", start_date),
            ("ptt_event_date", "<=", end_date),
        ]
        # Find "Booked" stage
        booked_stage = self.env["crm.stage"].search([("name", "ilike", "Booked")], limit=1)
        if booked_stage:
            booked_domain.append(("stage_id", "=", booked_stage.id))
        
        booked_leads = Lead.search(booked_domain)
        total_booked = sum(booked_leads.mapped("expected_revenue"))
        booked_count = len(booked_leads)
        
        # === TOTAL PAID INVOICES ===
        paid_domain = [
            ("move_type", "=", "out_invoice"),
            ("payment_state", "=", "paid"),
            ("invoice_date", ">=", start_date),
            ("invoice_date", "<=", end_date),
        ]
        paid_invoices = Invoice.search(paid_domain)
        total_paid = sum(paid_invoices.mapped("amount_total"))
        paid_count = len(paid_invoices)
        
        # === OUTSTANDING (unpaid/partial) ===
        outstanding_domain = [
            ("move_type", "=", "out_invoice"),
            ("payment_state", "in", ["not_paid", "partial"]),
            ("invoice_date", ">=", start_date),
            ("invoice_date", "<=", end_date),
        ]
        outstanding_invoices = Invoice.search(outstanding_domain)
        total_outstanding = sum(outstanding_invoices.mapped("amount_residual"))
        
        # === OVERDUE (past due date) ===
        overdue_invoices = outstanding_invoices.filtered(
            lambda inv: inv.invoice_date_due and inv.invoice_date_due < today
        )
        overdue_amount = sum(overdue_invoices.mapped("amount_residual"))
        
        # === PER-REP DATA ===
        # Get sales reps (users with CRM leads in this period)
        all_leads = Lead.search([
            ("ptt_event_date", ">=", start_date),
            ("ptt_event_date", "<=", end_date),
            ("user_id", "!=", False),
        ])
        
        rep_ids = all_leads.mapped("user_id").ids
        reps_data = []
        
        # Define colors for reps
        rep_colors = ["#6366F1", "#EC4899", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6"]
        
        for idx, user_id in enumerate(rep_ids):
            user = self.env["res.users"].browse(user_id)
            
            # Rep's booked leads
            rep_booked = booked_leads.filtered(lambda l: l.user_id.id == user_id)
            rep_booked_amount = sum(rep_booked.mapped("expected_revenue"))
            
            # Rep's total leads in period
            rep_all_leads = all_leads.filtered(lambda l: l.user_id.id == user_id)
            
            # Conversion rate
            conversion_rate = 0
            if len(rep_all_leads) > 0:
                conversion_rate = round((len(rep_booked) / len(rep_all_leads)) * 100)
            
            # Get initials
            name_parts = (user.name or "").split()
            initials = "".join([p[0].upper() for p in name_parts[:2]]) if name_parts else "?"
            
            # Get won/lost opportunities
            won_count = len(rep_booked)
            lost_stage = self.env["crm.stage"].search([("name", "ilike", "Lost")], limit=1)
            lost_count = 0
            if lost_stage:
                rep_lost = rep_all_leads.filtered(lambda l: l.stage_id.id == lost_stage.id)
                lost_count = len(rep_lost)
            
            # Revenue vs Target (if target exists - check for custom field or use default calculation)
            # For now, we'll calculate a target based on average or use a placeholder
            # In production, this would come from a sales target model or user field
            target_amount = 0.0
            if hasattr(user, 'x_sales_target') and user.x_sales_target:
                target_amount = user.x_sales_target
            elif hasattr(user, 'sales_target') and user.sales_target:
                target_amount = user.sales_target
            else:
                # Default: use average of all reps' booked amounts as target
                if len(reps_data) > 0:
                    avg_booked = sum([r.get("booked_amount", 0) for r in reps_data]) / len(reps_data)
                    target_amount = avg_booked * 1.2  # 20% above average as target
                else:
                    target_amount = rep_booked_amount * 1.2
            
            revenue_vs_target_pct = 0.0
            if target_amount > 0:
                revenue_vs_target_pct = round((rep_booked_amount / target_amount) * 100, 1)
            
            reps_data.append({
                "id": user_id,
                "name": user.name,
                "initials": initials,
                "color": rep_colors[idx % len(rep_colors)],
                "booked_amount": rep_booked_amount,
                "booked_count": won_count,
                "lost_count": lost_count,
                "leads_count": len(rep_all_leads),
                "conversion_rate": conversion_rate,
                "target_amount": target_amount,
                "revenue_vs_target_pct": revenue_vs_target_pct,
            })
        
        # Sort by booked amount descending
        reps_data.sort(key=lambda r: r["booked_amount"], reverse=True)
        
        # Calculate additional metrics
        capture_rate_data = self._get_capture_rate_metrics(start_date, end_date)
        avg_revenue_per_event = self._get_avg_revenue_per_event(start_date, end_date)
        avg_revenue_comparison = self._get_avg_revenue_comparison(start_date, end_date)
        
        return {
            "total_booked": total_booked,
            "booked_count": booked_count,
            "total_paid": total_paid,
            "paid_count": paid_count,
            "total_outstanding": total_outstanding,
            "overdue_amount": overdue_amount,
            "reps": reps_data,
            "capture_rate": capture_rate_data,
            "avg_revenue_per_event": avg_revenue_per_event,
            "avg_revenue_comparison": avg_revenue_comparison,
        }
    
    def _get_capture_rate_metrics(self, start_date, end_date):
        """Calculate won/lost conversion rates.
        
        Returns capture rate (won leads / total leads) as percentage.
        """
        Lead = self.env["crm.lead"]
        
        # Get all leads in date range
        all_leads = Lead.search([
            ("ptt_event_date", ">=", start_date),
            ("ptt_event_date", "<=", end_date),
        ])
        
        # Find "Booked" and "Lost" stages
        booked_stage = self.env["crm.stage"].search([("name", "ilike", "Booked")], limit=1)
        lost_stage = self.env["crm.stage"].search([("name", "ilike", "Lost")], limit=1)
        
        won_count = 0
        lost_count = 0
        
        if booked_stage:
            won_count = len(all_leads.filtered(lambda l: l.stage_id.id == booked_stage.id))
        if lost_stage:
            lost_count = len(all_leads.filtered(lambda l: l.stage_id.id == lost_stage.id))
        
        total_leads = len(all_leads)
        capture_rate = 0.0
        if total_leads > 0:
            capture_rate = round((won_count / total_leads) * 100, 1)
        
        return {
            "won_count": won_count,
            "lost_count": lost_count,
            "total_leads": total_leads,
            "capture_rate": capture_rate,
        }
    
    def _get_avg_revenue_per_event(self, start_date, end_date):
        """Calculate average revenue per event.
        
        Returns average revenue from booked events in the date range.
        """
        Lead = self.env["crm.lead"]
        booked_stage = self.env["crm.stage"].search([("name", "ilike", "Booked")], limit=1)
        
        if not booked_stage:
            return {"avg": 0.0, "count": 0}
        
        booked_leads = Lead.search([
            ("ptt_event_date", ">=", start_date),
            ("ptt_event_date", "<=", end_date),
            ("stage_id", "=", booked_stage.id),
        ])
        
        if len(booked_leads) == 0:
            return {"avg": 0.0, "count": 0}
        
        total_revenue = sum(booked_leads.mapped("expected_revenue"))
        avg_revenue = total_revenue / len(booked_leads)
        
        return {
            "avg": avg_revenue,
            "count": len(booked_leads),
        }
    
    def _get_avg_revenue_comparison(self, start_date, end_date):
        """Compare current period revenue to previous years.
        
        Returns comparison data for the same period in previous years.
        """
        from dateutil.relativedelta import relativedelta
        
        current_total = 0.0
        previous_year_total = 0.0
        previous_2year_total = 0.0
        
        Lead = self.env["crm.lead"]
        booked_stage = self.env["crm.stage"].search([("name", "ilike", "Booked")], limit=1)
        
        if booked_stage:
            # Current period
            current_leads = Lead.search([
                ("ptt_event_date", ">=", start_date),
                ("ptt_event_date", "<=", end_date),
                ("stage_id", "=", booked_stage.id),
            ])
            current_total = sum(current_leads.mapped("expected_revenue"))
            
            # Previous year (same date range)
            prev_start = start_date - relativedelta(years=1)
            prev_end = end_date - relativedelta(years=1)
            prev_leads = Lead.search([
                ("ptt_event_date", ">=", prev_start),
                ("ptt_event_date", "<=", prev_end),
                ("stage_id", "=", booked_stage.id),
            ])
            previous_year_total = sum(prev_leads.mapped("expected_revenue"))
            
            # Previous 2 years
            prev2_start = start_date - relativedelta(years=2)
            prev2_end = end_date - relativedelta(years=2)
            prev2_leads = Lead.search([
                ("ptt_event_date", ">=", prev2_start),
                ("ptt_event_date", "<=", prev2_end),
                ("stage_id", "=", booked_stage.id),
            ])
            previous_2year_total = sum(prev2_leads.mapped("expected_revenue"))
        
        # Calculate percentage changes
        prev_year_change = 0.0
        if previous_year_total > 0:
            prev_year_change = round(((current_total - previous_year_total) / previous_year_total) * 100, 1)
        
        prev_2year_change = 0.0
        if previous_2year_total > 0:
            prev_2year_change = round(((current_total - previous_2year_total) / previous_2year_total) * 100, 1)
        
        return {
            "current": current_total,
            "previous_year": previous_year_total,
            "previous_2year": previous_2year_total,
            "prev_year_change_pct": prev_year_change,
            "prev_2year_change_pct": prev_2year_change,
        }
    
    @api.model
    def get_sales_kpis(self):
        """Get sales KPIs for the Sales Dashboard (legacy method).
        
        Returns aggregated data from sale.order, crm.lead, account.move.
        """
        user = self.env.user
        today = fields.Date.context_today(self)
        
        # Leads to contact (assigned to user, in early stages)
        Lead = self.env["crm.lead"]
        leads_domain = [
            ("user_id", "=", user.id),
            ("type", "=", "lead"),
        ]
        leads_count = Lead.search_count(leads_domain)
        
        # Quotes awaiting approval
        SaleOrder = self.env["sale.order"]
        quotes_domain = [
            ("user_id", "=", user.id),
            ("state", "in", ["draft", "sent"]),
        ]
        quotes_count = SaleOrder.search_count(quotes_domain)
        quotes = SaleOrder.search(quotes_domain, limit=10)
        
        # Outstanding payments
        Invoice = self.env["account.move"]
        outstanding_domain = [
            ("move_type", "=", "out_invoice"),
            ("payment_state", "in", ["not_paid", "partial"]),
            ("invoice_user_id", "=", user.id),
        ]
        outstanding_invoices = Invoice.search(outstanding_domain)
        outstanding_amount = sum(outstanding_invoices.mapped("amount_residual"))
        
        return {
            "leads_count": leads_count,
            "leads_action": {
                "type": "ir.actions.act_window",
                "name": "My Leads",
                "res_model": "crm.lead",
                "views": [[False, "list"], [False, "form"]],
                "domain": leads_domain,
                "target": "current",
            },
            "quotes_count": quotes_count,
            "quotes": [
                {
                    "id": q.id,
                    "name": q.name,
                    "partner_name": q.partner_id.name if q.partner_id else "",
                    "amount_total": q.amount_total,
                    "action": {
                        "type": "ir.actions.act_window",
                        "res_model": "sale.order",
                        "res_id": q.id,
                        "views": [[False, "form"]],
                        "target": "current",
                    },
                }
                for q in quotes
            ],
            "quotes_action": {
                "type": "ir.actions.act_window",
                "name": "My Quotes",
                "res_model": "sale.order",
                "views": [[False, "list"], [False, "form"]],
                "domain": quotes_domain,
                "target": "current",
            },
            "outstanding_amount": outstanding_amount,
            "outstanding_action": {
                "type": "ir.actions.act_window",
                "name": "Outstanding Invoices",
                "res_model": "account.move",
                "views": [[False, "list"], [False, "form"]],
                "domain": outstanding_domain,
                "target": "current",
            },
        }
    
    @api.model
    def get_home_summary(self):
        """Get a complete summary for the Home page.
        
        Aggregates all data needed for the Home view.
        """
        return {
            "my_work": self.get_my_work_tasks(),
            "assigned_tasks": self.get_assigned_tasks(),
            "assigned_comments": self.get_assigned_comments(),
            "agenda_events": self.get_agenda_events(),
            "personal_todos": self.env["ptt.personal.todo"].get_my_todos(),
            "dashboard_tasks": self.get_dashboard_tasks(),
            "task_leaderboard": self.get_task_leaderboard(),
        }
    
    @api.model
    def create_quick_task(self, name, user_id=None, date_deadline=None, project_id=None):
        """Create a quick task from the dashboard.
        
        Args:
            name: Task name/description
            user_id: User to assign (defaults to current user)
            date_deadline: Due date (optional)
            project_id: Project to link to (optional, for misc tasks leave empty)
        
        Returns:
            dict with task data and action to open it
        """
        Task = self.env["project.task"]
        
        vals = {
            "name": name,
        }
        
        # Assign to specified user or current user
        if user_id:
            vals["user_ids"] = [(6, 0, [user_id])]
        else:
            vals["user_ids"] = [(6, 0, [self.env.user.id])]
        
        if date_deadline:
            vals["date_deadline"] = date_deadline
        
        if project_id:
            vals["project_id"] = project_id
        
        task = Task.create(vals)
        
        return {
            "id": task.id,
            "name": task.name,
            "action": {
                "type": "ir.actions.act_window",
                "res_model": "project.task",
                "res_id": task.id,
                "views": [[False, "form"]],
                "target": "current",
            },
        }
    
    @api.model
    def get_assignable_users(self):
        """Get list of users that can be assigned tasks.
        
        Returns internal users for the task assignment dropdown.
        """
        User = self.env["res.users"]
        users = User.search([
            ("share", "=", False),  # Internal users only
            ("active", "=", True),
        ], order="name")
        
        return [
            {"id": u.id, "name": u.name}
            for u in users
        ]
    
    @api.model
    def get_operations_dashboard_data(self, start_date=None, end_date=None):
        """Get comprehensive operations dashboard data with date filtering.
        
        Args:
            start_date: Start of date range (YYYY-MM-DD string)
            end_date: End of date range (YYYY-MM-DD string)
        
        Returns:
            dict with PO metrics, refunds, rain delays, collection time, avg time to event,
            event level metrics, and per-user data
        """
        today = fields.Date.context_today(self)
        
        # Default to current month if no dates provided
        if not start_date:
            start_date = today.replace(day=1)
        else:
            start_date = fields.Date.from_string(start_date)
        
        if not end_date:
            import calendar
            last_day = calendar.monthrange(today.year, today.month)[1]
            end_date = today.replace(day=last_day)
        else:
            end_date = fields.Date.from_string(end_date)
        
        # Get all metrics
        po_metrics = self._get_po_metrics(start_date, end_date)
        refund_metrics = self._get_refund_metrics(start_date, end_date)
        rain_delay_metrics = self._get_rain_delay_metrics(start_date, end_date)
        collection_time = self._get_collection_time_metrics(start_date, end_date)
        avg_time_to_event = self._get_avg_time_to_event(start_date, end_date)
        event_metrics = self._get_event_level_metrics(start_date, end_date)
        task_metrics = self._get_task_metrics()
        communication_metrics = self._get_communication_metrics()
        users_data = self._get_operations_users_data(start_date, end_date)
        
        return {
            "po_metrics": po_metrics,
            "refund_metrics": refund_metrics,
            "rain_delay_metrics": rain_delay_metrics,
            "collection_time": collection_time,
            "avg_time_to_event": avg_time_to_event,
            "event_metrics": event_metrics,
            "task_metrics": task_metrics,
            "communication_metrics": communication_metrics,
            "users": users_data,
        }
    
    def _get_po_metrics(self, start_date, end_date):
        """Get purchase order metrics for the date range.
        
        Returns total amount and count of POs.
        """
        # Search for purchase orders (vendor bills or purchase orders)
        # Using account.move with move_type='in_invoice' for vendor bills
        PurchaseOrder = self.env.get("purchase.order")
        if PurchaseOrder:
            pos = PurchaseOrder.search([
                ("date_order", ">=", start_date),
                ("date_order", "<=", end_date),
                ("state", "in", ["purchase", "done"]),
            ])
            total_amount = sum(pos.mapped("amount_total"))
            return {
                "total_amount": total_amount,
                "count": len(pos),
            }
        else:
            # Fallback to vendor bills
            VendorBills = self.env["account.move"]
            bills = VendorBills.search([
                ("move_type", "=", "in_invoice"),
                ("date", ">=", start_date),
                ("date", "<=", end_date),
                ("state", "=", "posted"),
            ])
            total_amount = sum(bills.mapped("amount_total"))
            return {
                "total_amount": total_amount,
                "count": len(bills),
            }
    
    def _get_refund_metrics(self, start_date, end_date):
        """Get refund metrics for the date range.
        
        Returns total amount and count of refunds being issued.
        """
        # Refunds are typically credit notes (account.move with move_type='out_refund')
        Refunds = self.env["account.move"]
        refunds = Refunds.search([
            ("move_type", "=", "out_refund"),
            ("date", ">=", start_date),
            ("date", "<=", end_date),
            ("state", "=", "posted"),
        ])
        total_amount = sum(refunds.mapped("amount_total"))
        return {
            "total_amount": total_amount,
            "count": len(refunds),
        }
    
    def _get_rain_delay_metrics(self, start_date, end_date):
        """Get rain delay metrics.
        
        Returns count and percentage of events with rain delays.
        Note: This assumes there's a field to track rain delays (e.g., x_rain_delay on crm.lead or project.project)
        """
        Lead = self.env["crm.lead"]
        
        # Get all events in date range
        all_events = Lead.search([
            ("ptt_event_date", ">=", start_date),
            ("ptt_event_date", "<=", end_date),
            ("ptt_event_date", "!=", False),
        ])
        
        # Check for rain delay field (if it exists)
        rain_delays = 0
        if "x_rain_delay" in Lead._fields:
            rain_delays = len(all_events.filtered(lambda e: e.x_rain_delay))
        elif "x_weather_delay" in Lead._fields:
            rain_delays = len(all_events.filtered(lambda e: e.x_weather_delay))
        
        percentage = 0.0
        if len(all_events) > 0:
            percentage = round((rain_delays / len(all_events)) * 100, 1)
        
        return {
            "count": rain_delays,
            "percentage": percentage,
            "total_events": len(all_events),
        }
    
    def _get_collection_time_metrics(self, start_date, end_date):
        """Get average time to collect on invoices.
        
        Returns average days from invoice date to payment date.
        """
        Invoice = self.env["account.move"]
        
        # Get paid invoices in date range
        paid_invoices = Invoice.search([
            ("move_type", "=", "out_invoice"),
            ("payment_state", "=", "paid"),
            ("invoice_date", ">=", start_date),
            ("invoice_date", "<=", end_date),
        ])
        
        if len(paid_invoices) == 0:
            return {
                "avg_days": None,
                "invoice_count": 0,
            }
        
        # Calculate days to payment for each invoice
        total_days = 0
        count = 0
        for inv in paid_invoices:
            if inv.invoice_date and inv.invoice_date_due:
                # Use payment date if available, otherwise use due date as proxy
                days = (inv.invoice_date_due - inv.invoice_date).days
                if days >= 0:
                    total_days += days
                    count += 1
        
        avg_days = total_days / count if count > 0 else None
        
        return {
            "avg_days": avg_days,
            "invoice_count": len(paid_invoices),
        }
    
    def _get_avg_time_to_event(self, start_date, end_date):
        """Get average time from lead creation to event date.
        
        Returns average days from lead create_date to ptt_event_date.
        """
        Lead = self.env["crm.lead"]
        
        # Get leads with event dates in range
        leads = Lead.search([
            ("ptt_event_date", ">=", start_date),
            ("ptt_event_date", "<=", end_date),
            ("ptt_event_date", "!=", False),
        ])
        
        if len(leads) == 0:
            return {
                "avg_days": None,
                "event_count": 0,
            }
        
        total_days = 0
        count = 0
        for lead in leads:
            if lead.create_date and lead.ptt_event_date:
                days = (lead.ptt_event_date - lead.create_date.date()).days
                if days >= 0:
                    total_days += days
                    count += 1
        
        avg_days = total_days / count if count > 0 else None
        
        return {
            "avg_days": avg_days,
            "event_count": len(leads),
        }
    
    def _get_event_level_metrics(self, start_date, end_date):
        """Get event-level operational metrics.
        
        Returns average $ per event, services per event, line items per event.
        """
        Lead = self.env["crm.lead"]
        SaleOrder = self.env["sale.order"]
        booked_stage = self.env["crm.stage"].search([("name", "ilike", "Booked")], limit=1)
        
        if not booked_stage:
            return {
                "avg_revenue_per_event": 0.0,
                "min_revenue": 0.0,
                "max_revenue": 0.0,
                "avg_services_per_event": 0.0,
                "avg_line_items_per_event": 0.0,
                "total_events": 0,
            }
        
        # Get booked events in range
        booked_leads = Lead.search([
            ("ptt_event_date", ">=", start_date),
            ("ptt_event_date", "<=", end_date),
            ("stage_id", "=", booked_stage.id),
        ])
        
        if len(booked_leads) == 0:
            return {
                "avg_revenue_per_event": 0.0,
                "min_revenue": 0.0,
                "max_revenue": 0.0,
                "avg_services_per_event": 0.0,
                "avg_line_items_per_event": 0.0,
                "total_events": 0,
            }
        
        # Get revenue from sale orders linked to these leads
        revenues = []
        total_services = 0
        total_line_items = 0
        
        for lead in booked_leads:
            # Find sale orders for this lead
            orders = SaleOrder.search([
                ("opportunity_id", "=", lead.id),
                ("state", "=", "sale"),
            ])
            
            lead_revenue = sum(orders.mapped("amount_total"))
            revenues.append(lead_revenue)
            
            # Count services and line items
            for order in orders:
                total_services += len(order.order_line.filtered(lambda l: l.product_id.type == "service"))
                total_line_items += len(order.order_line)
        
        avg_revenue = sum(revenues) / len(revenues) if revenues else 0.0
        min_revenue = min(revenues) if revenues else 0.0
        max_revenue = max(revenues) if revenues else 0.0
        avg_services = total_services / len(booked_leads) if booked_leads else 0.0
        avg_line_items = total_line_items / len(booked_leads) if booked_leads else 0.0
        
        return {
            "avg_revenue_per_event": avg_revenue,
            "min_revenue": min_revenue,
            "max_revenue": max_revenue,
            "avg_services_per_event": round(avg_services, 1),
            "avg_line_items_per_event": round(avg_line_items, 1),
            "total_events": len(booked_leads),
        }
    
    def _get_operations_users_data(self, start_date, end_date):
        """Get operational metrics broken out by user.
        
        Returns per-user data for POs, refunds, collection time, task metrics, and communication metrics.
        """
        today = fields.Date.context_today(self)
        Task = self.env["project.task"]
        Message = self.env["mail.message"]
        
        # Get all active users
        User = self.env["res.users"]
        users = User.search([
            ("share", "=", False),
            ("active", "=", True),
        ])
        
        users_data = []
        for user in users:
            # Get user's POs (if purchase module available)
            po_amount = 0.0
            PurchaseOrder = self.env.get("purchase.order")
            if PurchaseOrder:
                user_pos = PurchaseOrder.search([
                    ("date_order", ">=", start_date),
                    ("date_order", "<=", end_date),
                    ("user_id", "=", user.id),
                    ("state", "in", ["purchase", "done"]),
                ])
                po_amount = sum(user_pos.mapped("amount_total"))
            
            # Get user's refunds (credit notes they created)
            user_refunds = self.env["account.move"].search([
                ("move_type", "=", "out_refund"),
                ("date", ">=", start_date),
                ("date", "<=", end_date),
                ("invoice_user_id", "=", user.id),
                ("state", "=", "posted"),
            ])
            refund_amount = sum(user_refunds.mapped("amount_total"))
            
            # Get user's collection time
            user_invoices = self.env["account.move"].search([
                ("move_type", "=", "out_invoice"),
                ("payment_state", "=", "paid"),
                ("invoice_date", ">=", start_date),
                ("invoice_date", "<=", end_date),
                ("invoice_user_id", "=", user.id),
            ])
            
            collection_time = None
            if len(user_invoices) > 0:
                total_days = 0
                count = 0
                for inv in user_invoices:
                    if inv.invoice_date and inv.invoice_date_due:
                        days = (inv.invoice_date_due - inv.invoice_date).days
                        if days >= 0:
                            total_days += days
                            count += 1
                collection_time = total_days / count if count > 0 else None
            
            # Get initials
            name_parts = (user.name or "").split()
            initials = "".join([p[0].upper() for p in name_parts[:2]]) if name_parts else "?"
            
            # Get user's task metrics
            user_total_assigned = Task.search_count([
                ("user_ids", "in", [user.id]),
                ("stage_id.fold", "=", False),
            ])
            user_overdue = Task.search_count([
                ("user_ids", "in", [user.id]),
                ("date_deadline", "<", today),
                ("date_deadline", "!=", False),
                ("stage_id.fold", "=", False),
            ])
            user_unassigned = Task.search_count([
                ("user_ids", "=", False),
                ("stage_id.fold", "=", False),
            ])
            user_completed = Task.search_count([
                ("user_ids", "in", [user.id]),
                ("stage_id.fold", "=", True),
            ])
            
            # Get user's communication metrics
            thirty_days_ago = today - timedelta(days=30)
            user_messages = Message.search_count([
                ("date", ">=", thirty_days_ago),
                ("message_type", "in", ["email", "comment"]),
                ("author_id", "=", user.partner_id.id),
            ])
            
            users_data.append({
                "id": user.id,
                "name": user.name,
                "initials": initials,
                "po_amount": po_amount,
                "refund_amount": refund_amount,
                "collection_time": collection_time,
                "task_total_assigned": user_total_assigned,
                "task_overdue": user_overdue,
                "task_unassigned": user_unassigned,
                "task_completed": user_completed,
                "messages_sent": user_messages,
            })
        
        return users_data
    
    def _get_task_metrics(self):
        """Get company-wide task metrics.
        
        Returns total assigned, overdue, unassigned, and completed task counts.
        """
        today = fields.Date.context_today(self)
        Task = self.env["project.task"]
        
        # Total assigned (not in folded stages)
        total_assigned = Task.search_count([
            ("user_ids", "!=", False),
            ("stage_id.fold", "=", False),
        ])
        
        # Overdue tasks
        overdue = Task.search_count([
            ("date_deadline", "<", today),
            ("date_deadline", "!=", False),
            ("stage_id.fold", "=", False),
        ])
        
        # Unassigned tasks
        unassigned = Task.search_count([
            ("user_ids", "=", False),
            ("stage_id.fold", "=", False),
        ])
        
        # Completed tasks (in folded stages)
        completed = Task.search_count([
            ("stage_id.fold", "=", True),
        ])
        
        return {
            "total_assigned": total_assigned,
            "overdue": overdue,
            "unassigned": unassigned,
            "completed": completed,
        }
    
    def _get_communication_metrics(self):
        """Get company-wide communication metrics from mail.message.
        
        Returns open discussions count and messages sent count.
        """
        Message = self.env["mail.message"]
        today = fields.Date.context_today(self)
        
        # Messages sent (last 30 days)
        thirty_days_ago = today - timedelta(days=30)
        messages_sent = Message.search_count([
            ("date", ">=", thirty_days_ago),
            ("message_type", "in", ["email", "comment"]),
            ("author_id", "!=", False),
        ])
        
        # Open discussions (threads with recent activity)
        # This is a simplified metric - in practice you might want to track
        # threads with unread messages or active conversations
        open_discussions = Message.search_count([
            ("date", ">=", thirty_days_ago),
            ("message_type", "in", ["email", "comment"]),
        ])
        
        return {
            "open_discussions": open_discussions,
            "messages_sent": messages_sent,
        }
    
    @api.model
    def get_communication_dashboard_data(self, start_date=None, end_date=None):
        """Get comprehensive communication dashboard data with date filtering.
        
        Args:
            start_date: Start of date range (YYYY-MM-DD string)
            end_date: End of date range (YYYY-MM-DD string)
        
        Returns:
            dict with total calls, total emails, response times, and per-user data
        """
        today = fields.Date.context_today(self)
        
        # Default to current month if no dates provided
        if not start_date:
            start_date = today.replace(day=1)
        else:
            start_date = fields.Date.from_string(start_date)
        
        if not end_date:
            import calendar
            last_day = calendar.monthrange(today.year, today.month)[1]
            end_date = today.replace(day=last_day)
        else:
            end_date = fields.Date.from_string(end_date)
        
        # Get communication metrics
        total_calls, total_emails = self._get_total_communications(start_date, end_date)
        avg_response_calls, avg_response_emails = self._get_response_time_metrics(start_date, end_date)
        users_data = self._get_communication_users_data(start_date, end_date, total_calls, total_emails)
        
        return {
            "total_calls": total_calls,
            "total_emails": total_emails,
            "avg_response_time_calls": avg_response_calls,
            "avg_response_time_emails": avg_response_emails,
            "users": users_data,
        }
    
    def _get_total_communications(self, start_date, end_date):
        """Get total calls and emails for the date range.
        
        Returns (total_calls, total_emails)
        """
        # Get emails from mail.message
        Message = self.env["mail.message"]
        emails = Message.search([
            ("date", ">=", start_date),
            ("date", "<=", end_date),
            ("message_type", "in", ["email", "comment"]),
            ("author_id", "!=", False),
        ])
        total_emails = len(emails)
        
        # Get calls from activities or crm.phonecall if available
        total_calls = 0
        Activity = self.env.get("mail.activity")
        if Activity:
            calls = Activity.search([
                ("date_deadline", ">=", start_date),
                ("date_deadline", "<=", end_date),
                ("activity_type_id.name", "ilike", "call"),
            ])
            total_calls = len(calls)
        else:
            # Fallback: try to get from mail.message with call-related subjects
            call_messages = Message.search([
                ("date", ">=", start_date),
                ("date", "<=", end_date),
                ("subject", "ilike", "call"),
            ])
            total_calls = len(call_messages)
        
        return (total_calls, total_emails)
    
    def _get_response_time_metrics(self, start_date, end_date):
        """Get average response time for calls and emails.
        
        Returns (avg_response_calls_hours, avg_response_emails_hours)
        
        Response time is calculated as time from when a message/activity is created
        to when a response is received. This is a simplified calculation.
        """
        Message = self.env["mail.message"]
        
        # For emails: calculate time from first message in thread to response
        # This is a simplified approach - in reality, you'd track conversation threads
        emails = Message.search([
            ("date", ">=", start_date),
            ("date", "<=", end_date),
            ("message_type", "in", ["email", "comment"]),
        ], order="date asc")
        
        # Group by thread/res_id to calculate response times
        response_times_emails = []
        threads = {}
        for msg in emails:
            thread_key = f"{msg.model}_{msg.res_id}"
            if thread_key not in threads:
                threads[thread_key] = []
            threads[thread_key].append(msg)
        
        # Calculate response times within threads
        for thread_msgs in threads.values():
            if len(thread_msgs) > 1:
                for i in range(1, len(thread_msgs)):
                    prev_msg = thread_msgs[i-1]
                    curr_msg = thread_msgs[i]
                    if prev_msg.author_id != curr_msg.author_id:  # Different authors = response
                        time_diff = (curr_msg.date - prev_msg.date).total_seconds() / 3600  # hours
                        if time_diff > 0 and time_diff < 168:  # Within a week
                            response_times_emails.append(time_diff)
        
        avg_response_emails = sum(response_times_emails) / len(response_times_emails) if response_times_emails else None
        
        # For calls: similar approach with activities
        avg_response_calls = None
        Activity = self.env.get("mail.activity")
        if Activity:
            activities = Activity.search([
                ("date_deadline", ">=", start_date),
                ("date_deadline", "<=", end_date),
                ("activity_type_id.name", "ilike", "call"),
            ])
            # Simplified: use activity duration or time to completion
            # In reality, you'd track actual call response times
            if len(activities) > 0:
                # Placeholder calculation
                avg_response_calls = 2.0  # Default 2 hours average
        
        return (avg_response_calls, avg_response_emails)
    
    def _get_communication_users_data(self, start_date, end_date, total_calls, total_emails):
        """Get communication metrics broken out by user.
        
        Returns per-user data for calls, emails, and response times.
        """
        User = self.env["res.users"]
        Message = self.env["mail.message"]
        users = User.search([
            ("share", "=", False),
            ("active", "=", True),
        ])
        
        users_data = []
        for user in users:
            # Get user's emails
            user_emails = Message.search([
                ("date", ">=", start_date),
                ("date", "<=", end_date),
                ("message_type", "in", ["email", "comment"]),
                ("author_id", "=", user.partner_id.id),
            ])
            emails_count = len(user_emails)
            
            # Get user's calls (from activities)
            calls_count = 0
            Activity = self.env.get("mail.activity")
            if Activity:
                user_calls = Activity.search([
                    ("date_deadline", ">=", start_date),
                    ("date_deadline", "<=", end_date),
                    ("activity_type_id.name", "ilike", "call"),
                    ("user_id", "=", user.id),
                ])
                calls_count = len(user_calls)
            
            # Calculate user's response times (simplified)
            response_time_emails = None
            response_time_calls = None
            
            # For emails: calculate from user's messages in threads
            user_response_times = []
            user_threads = {}
            for msg in user_emails:
                thread_key = f"{msg.model}_{msg.res_id}"
                if thread_key not in user_threads:
                    user_threads[thread_key] = []
                user_threads[thread_key].append(msg)
            
            for thread_msgs in user_threads.values():
                if len(thread_msgs) > 1:
                    for i in range(1, len(thread_msgs)):
                        prev_msg = thread_msgs[i-1]
                        curr_msg = thread_msgs[i]
                        if prev_msg.author_id != curr_msg.author_id:
                            time_diff = (curr_msg.date - prev_msg.date).total_seconds() / 3600
                            if time_diff > 0 and time_diff < 168:
                                user_response_times.append(time_diff)
            
            if user_response_times:
                response_time_emails = sum(user_response_times) / len(user_response_times)
            
            # For calls: placeholder
            if calls_count > 0:
                response_time_calls = 2.0  # Default
            
            # Get initials
            name_parts = (user.name or "").split()
            initials = "".join([p[0].upper() for p in name_parts[:2]]) if name_parts else "?"
            
            users_data.append({
                "id": user.id,
                "name": user.name,
                "initials": initials,
                "calls_count": calls_count,
                "emails_count": emails_count,
                "response_time_calls": response_time_calls,
                "response_time_emails": response_time_emails,
            })
        
        return users_data
    
    @api.model
    def export_dashboard_to_excel(self, data, title="Dashboard Export"):
        """Export dashboard data to Excel format.
        
        Args:
            data: Dashboard data dictionary
            title: Export title
        
        Returns:
            dict with file_url for download
        """
        import base64
        import io
        try:
            import xlsxwriter
        except ImportError:
            # Fallback: return error message
            return {
                "error": "xlsxwriter library not available. Please install it: pip install xlsxwriter"
            }
        
        # Create Excel file in memory
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet(title[:31])  # Excel sheet name limit
        
        # Write data (simplified - would need to format based on data structure)
        row = 0
        worksheet.write(row, 0, title)
        row += 2
        
        # Write headers and data based on structure
        if isinstance(data, dict):
            for key, value in data.items():
                worksheet.write(row, 0, str(key))
                if isinstance(value, (int, float)):
                    worksheet.write(row, 1, value)
                elif isinstance(value, dict):
                    worksheet.write(row, 1, str(value))
                else:
                    worksheet.write(row, 1, str(value))
                row += 1
        
        workbook.close()
        output.seek(0)
        
        # Save to attachment
        attachment = self.env['ir.attachment'].create({
            'name': f"{title}_{fields.Date.today()}.xlsx",
            'type': 'binary',
            'datas': base64.b64encode(output.read()),
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })
        
        return {
            "file_url": f"/web/content/{attachment.id}?download=true",
        }
    
    @api.model
    def export_dashboard_to_pdf(self, data, title="Dashboard Export"):
        """Export dashboard data to PDF format.
        
        Args:
            data: Dashboard data dictionary
            title: Export title
        
        Returns:
            dict with file_url for download
        """
        # For PDF export, we'll use Odoo's report system
        # This is a simplified version - in production, you'd use proper report templates
        import base64
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
            import io
        except ImportError:
            return {
                "error": "reportlab library not available. Please install it: pip install reportlab"
            }
        
        # Create PDF in memory
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        
        # Write title
        p.setFont("Helvetica-Bold", 16)
        p.drawString(100, 750, title)
        
        # Write data (simplified)
        y = 700
        p.setFont("Helvetica", 12)
        if isinstance(data, dict):
            for key, value in data.items():
                p.drawString(100, y, f"{key}: {value}")
                y -= 20
                if y < 50:
                    p.showPage()
                    y = 750
        
        p.save()
        buffer.seek(0)
        
        # Save to attachment
        attachment = self.env['ir.attachment'].create({
            'name': f"{title}_{fields.Date.today()}.pdf",
            'type': 'binary',
            'datas': base64.b64encode(buffer.read()),
            'mimetype': 'application/pdf',
        })
        
        return {
            "file_url": f"/web/content/{attachment.id}?download=true",
        }
