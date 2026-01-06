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
        """Get EVENT tasks assigned to current user, categorized by due date.
        
        Only returns tasks from projects that are linked to CRM leads (event projects).
        These are event planning tasks like vendor coordination, client follow-up, etc.
        
        Categories: today, overdue, upcoming, unscheduled
        """
        user = self.env.user
        today = fields.Date.context_today(self)
        
        Task = self.env["project.task"]
        Project = self.env["project.project"]
        
        # First, get all projects linked to CRM leads (event projects)
        if "x_crm_lead_id" in Project._fields:
            event_project_ids = Project.search([
                ("x_crm_lead_id", "!=", False)
            ]).ids
        else:
            event_project_ids = []
        
        # Get tasks from event projects assigned to user
        domain = [
            ("user_ids", "in", [user.id]),
            ("stage_id.fold", "=", False),  # Not in folded/done stages
            ("project_id", "in", event_project_ids),  # Only from event projects
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
        
        Only returns tasks that are NOT from event projects (not linked to CRM leads).
        These are standalone tasks, internal tasks, or tasks from non-event projects.
        """
        user = self.env.user
        today = fields.Date.context_today(self)
        
        Task = self.env["project.task"]
        Project = self.env["project.project"]
        
        # Get projects that ARE linked to CRM leads (event projects) to EXCLUDE them
        event_project_ids = []
        if "x_crm_lead_id" in Project._fields:
            event_projects = Project.search([("x_crm_lead_id", "!=", False)])
            event_project_ids = event_projects.ids
        
        # Build domain: tasks assigned to user, not done, NOT from event projects
        # Using proper Odoo domain syntax with '|' at the start
        if event_project_ids:
            # Tasks with no project OR tasks from non-event projects
            domain = [
                ("user_ids", "in", [user.id]),
                ("stage_id.fold", "=", False),
                "|",
                ("project_id", "=", False),
                ("project_id", "not in", event_project_ids),
            ]
        else:
            # No event projects exist, show all tasks
            domain = [
                ("user_ids", "in", [user.id]),
                ("stage_id.fold", "=", False),
            ]
        
        tasks = Task.search(domain, order="date_deadline asc, project_id, id")
        
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
        
        Pulls from crm.lead where x_event_date is set and assigned to user.
        Shows events in the next N days (default 14).
        
        This shows the USER'S assigned events at ALL stages.
        For company-wide view, use the Event Calendar tab.
        """
        user = self.env.user
        today = fields.Date.context_today(self)
        end_date = today + timedelta(days=days)
        
        Lead = self.env["crm.lead"]
        
        # Check if x_event_date field exists on crm.lead
        if "x_event_date" not in Lead._fields:
            return []
        
        # Get leads assigned to user with event dates in range
        domain = [
            ("user_id", "=", user.id),
            ("x_event_date", ">=", today),
            ("x_event_date", "<=", end_date),
            ("x_event_date", "!=", False),
        ]
        
        leads = Lead.search(domain, order="x_event_date asc", limit=20)
        
        # PTT CRM Stage Colors
        stage_colors = {
            "New": "#17A2B8",
            "Qualified": "#007BFF",
            "Approval": "#FFC107",
            "Quote Sent": "#6F42C1",
            "Booked": "#28A745",
            "Lost": "#DC3545",
        }
        default_color = "#6C757D"
        
        result = []
        for lead in leads:
            stage_name = lead.stage_id.name if lead.stage_id else "Unknown"
            color = stage_colors.get(stage_name, default_color)
            event_name = lead.x_event_name or lead.name or "Untitled Event"
            
            event_data = {
                "id": lead.id,
                "name": event_name,
                "lead_name": lead.name,
                "event_date": lead.x_event_date.isoformat() if lead.x_event_date else False,
                "partner_name": lead.partner_id.name if lead.partner_id else (lead.partner_name or ""),
                "stage_name": stage_name,
                "color": color,
                "stage_id": lead.stage_id.id if lead.stage_id else False,
                # Action metadata - opens CRM Lead form
                "action": {
                    "type": "ir.actions.act_window",
                    "res_model": "crm.lead",
                    "res_id": lead.id,
                    "views": [[False, "form"]],
                    "target": "current",
                },
            }
            result.append(event_data)
        
        return result
    
    @api.model
    def get_event_calendar_data(self, start_date=None, end_date=None, my_events_only=False):
        """Get all CRM leads with event dates for the calendar view.
        
        Pulls from crm.lead where x_event_date is set.
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
        
        # Check if x_event_date field exists on crm.lead
        if "x_event_date" not in Lead._fields:
            return {"events": [], "stages": []}
        
        # Build domain - ALL events by default
        domain = [
            ("x_event_date", ">=", start_date),
            ("x_event_date", "<=", end_date),
            ("x_event_date", "!=", False),
        ]
        
        # Filter to user's events if requested
        if my_events_only:
            domain.append(("user_id", "=", user.id))
        
        leads = Lead.search(domain, order="x_event_date asc")
        
        # PTT CRM Stage Colors
        # These are the official PTT pipeline stages
        # Stages: New, Qualified, Approval, Quote Sent, Booked, Lost
        stage_colors = {
            "New": "#17A2B8",           # Teal/Cyan - New inquiries
            "Qualified": "#F97316",     # Orange - Qualified leads
            "Approval": "#FFC107",      # Yellow/Amber - Awaiting approval
            "Quote Sent": "#6F42C1",    # Purple - Quote sent
            "Booked": "#28A745",        # Green - Confirmed bookings
            "Lost": "#DC3545",          # Red - Lost opportunities
        }
        default_color = "#6C757D"  # Gray for unknown stages
        
        events = []
        for lead in leads:
            stage_name = lead.stage_id.name if lead.stage_id else "Unknown"
            color = stage_colors.get(stage_name, default_color)
            
            # Get event display name
            event_name = lead.x_event_name or lead.name or "Untitled Event"
            
            # Get assignee info
            assignee_name = lead.user_id.name if lead.user_id else "Unassigned"
            is_mine = lead.user_id.id == user.id if lead.user_id else False
            
            event_data = {
                "id": lead.id,
                "name": event_name,
                "lead_name": lead.name,
                "event_date": lead.x_event_date.isoformat() if lead.x_event_date else False,
                "event_time": lead.x_event_time if hasattr(lead, 'x_event_time') else "",
                "partner_name": lead.partner_id.name if lead.partner_id else (lead.partner_name or ""),
                "contact_name": lead.contact_name or "",
                "stage_id": lead.stage_id.id if lead.stage_id else False,
                "stage_name": stage_name,
                "color": color,
                "event_type": lead.x_event_type if hasattr(lead, 'x_event_type') else "",
                "venue_name": lead.x_venue_name if hasattr(lead, 'x_venue_name') else "",
                "guest_count": lead.x_estimated_guest_count if hasattr(lead, 'x_estimated_guest_count') else 0,
                "assignee_id": lead.user_id.id if lead.user_id else False,
                "assignee_name": assignee_name,
                "is_mine": is_mine,
                # Project link if exists
                "project_id": lead.x_project_id.id if hasattr(lead, 'x_project_id') and lead.x_project_id else False,
                "project_name": lead.x_project_id.name if hasattr(lead, 'x_project_id') and lead.x_project_id else "",
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
                    "res_id": lead.x_project_id.id,
                    "views": [[False, "form"]],
                    "target": "current",
                } if hasattr(lead, 'x_project_id') and lead.x_project_id else None,
            }
            events.append(event_data)
        
        # Get all stages for the legend
        stages = self._get_crm_stages_with_colors(stage_colors, default_color)
        
        return {
            "events": events,
            "stages": stages,
            "current_user_id": user.id,
        }
    
    @api.model
    def _get_crm_stages_with_colors(self, stage_colors, default_color):
        """Get all CRM stages with their colors for the calendar legend."""
        Stage = self.env["crm.stage"]
        stages = Stage.search([], order="sequence")
        
        result = []
        for stage in stages:
            result.append({
                "id": stage.id,
                "name": stage.name,
                "color": stage_colors.get(stage.name, default_color),
                "sequence": stage.sequence,
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
        
        if "x_event_date" not in Lead._fields:
            return []
        
        domain = [
            ("x_event_date", "=", event_date),
        ]
        
        if my_events_only:
            domain.append(("user_id", "=", user.id))
        
        leads = Lead.search(domain, order="x_event_time asc, name asc")
        
        stage_colors = {
            "New": "#17A2B8",
            "Qualified": "#007BFF",
            "Approval": "#FFC107",
            "Quote Sent": "#6F42C1",
            "Booked": "#28A745",
            "Lost": "#DC3545",
        }
        default_color = "#6C757D"
        
        events = []
        for lead in leads:
            stage_name = lead.stage_id.name if lead.stage_id else "Unknown"
            event_name = lead.x_event_name or lead.name or "Untitled Event"
            
            events.append({
                "id": lead.id,
                "name": event_name,
                "lead_name": lead.name,
                "event_time": lead.x_event_time if hasattr(lead, 'x_event_time') else "",
                "partner_name": lead.partner_id.name if lead.partner_id else (lead.partner_name or ""),
                "stage_name": stage_name,
                "color": stage_colors.get(stage_name, default_color),
                "venue_name": lead.x_venue_name if hasattr(lead, 'x_venue_name') else "",
                "assignee_name": lead.user_id.name if lead.user_id else "Unassigned",
                "is_mine": lead.user_id.id == user.id if lead.user_id else False,
                "action": {
                    "type": "ir.actions.act_window",
                    "res_model": "crm.lead",
                    "res_id": lead.id,
                    "views": [[False, "form"]],
                    "target": "current",
                },
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
            ("x_event_date", ">=", start_date),
            ("x_event_date", "<=", end_date),
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
            ("x_event_date", ">=", start_date),
            ("x_event_date", "<=", end_date),
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
            
            reps_data.append({
                "id": user_id,
                "name": user.name,
                "initials": initials,
                "color": rep_colors[idx % len(rep_colors)],
                "booked_amount": rep_booked_amount,
                "booked_count": len(rep_booked),
                "leads_count": len(rep_all_leads),
                "conversion_rate": conversion_rate,
            })
        
        # Sort by booked amount descending
        reps_data.sort(key=lambda r: r["booked_amount"], reverse=True)
        
        return {
            "total_booked": total_booked,
            "booked_count": booked_count,
            "total_paid": total_paid,
            "paid_count": paid_count,
            "total_outstanding": total_outstanding,
            "overdue_amount": overdue_amount,
            "reps": reps_data,
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
