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
        """Get tasks assigned to current user, categorized by due date.
        
        Returns tasks from project.task with action metadata for deep linking.
        Categories: today, overdue, upcoming, unscheduled
        """
        user = self.env.user
        today = fields.Date.context_today(self)
        
        # Get all open tasks assigned to user
        Task = self.env["project.task"]
        domain = [
            ("user_ids", "in", [user.id]),
            ("stage_id.fold", "=", False),  # Not in folded/done stages
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
        """Get all tasks assigned to current user with full hierarchy info.
        
        Returns tasks organized by due date with links to parent project and CRM lead.
        """
        user = self.env.user
        today = fields.Date.context_today(self)
        
        Task = self.env["project.task"]
        domain = [
            ("user_ids", "in", [user.id]),
            ("stage_id.fold", "=", False),
        ]
        tasks = Task.search(domain, order="date_deadline asc, project_id, id")
        
        result = []
        for task in tasks:
            # Get CRM lead if project has one
            crm_lead = None
            crm_lead_action = None
            if task.project_id and hasattr(task.project_id, 'x_crm_lead_id') and task.project_id.x_crm_lead_id:
                lead = task.project_id.x_crm_lead_id
                crm_lead = {
                    "id": lead.id,
                    "name": lead.name,
                }
                crm_lead_action = {
                    "type": "ir.actions.act_window",
                    "res_model": "crm.lead",
                    "res_id": lead.id,
                    "views": [[False, "form"]],
                    "target": "current",
                }
            
            task_data = {
                "id": task.id,
                "name": task.name,
                "date_deadline": task.date_deadline.isoformat() if task.date_deadline else False,
                "is_overdue": task.date_deadline and task.date_deadline < today,
                "priority": task.priority,
                "stage_name": task.stage_id.name if task.stage_id else "",
                "project_id": task.project_id.id if task.project_id else False,
                "project_name": task.project_id.name if task.project_id else "",
                "crm_lead": crm_lead,
                "crm_lead_action": crm_lead_action,
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
        """Get upcoming events/projects for the current user's agenda.
        
        Returns project.project records with x_event_date in the next N days.
        """
        user = self.env.user
        today = fields.Date.context_today(self)
        end_date = today + timedelta(days=days)
        
        Project = self.env["project.project"]
        domain = [
            ("user_id", "=", user.id),
            ("x_event_date", ">=", today),
            ("x_event_date", "<=", end_date),
        ]
        
        # Check if x_event_date field exists
        if "x_event_date" not in Project._fields:
            return []
        
        projects = Project.search(domain, order="x_event_date asc")
        
        result = []
        for project in projects:
            # Get CRM lead stage for color coding
            lead_stage = None
            if hasattr(project, 'x_crm_lead_id') and project.x_crm_lead_id:
                lead = project.x_crm_lead_id
                lead_stage = {
                    "id": lead.stage_id.id if lead.stage_id else False,
                    "name": lead.stage_id.name if lead.stage_id else "",
                }
            
            event_data = {
                "id": project.id,
                "name": project.name,
                "event_date": project.x_event_date.isoformat() if project.x_event_date else False,
                "partner_name": project.partner_id.name if project.partner_id else "",
                "lead_stage": lead_stage,
                # Action metadata
                "action": {
                    "type": "ir.actions.act_window",
                    "res_model": "project.project",
                    "res_id": project.id,
                    "views": [[False, "form"]],
                    "target": "current",
                },
            }
            result.append(event_data)
        
        return result
    
    @api.model
    def get_event_calendar_data(self, start_date=None, end_date=None):
        """Get all events for the calendar view with status colors.
        
        Returns project.project records with CRM lead stage for coloring.
        """
        today = fields.Date.context_today(self)
        if not start_date:
            start_date = today.replace(day=1)
        if not end_date:
            # End of next month
            if today.month == 12:
                end_date = today.replace(year=today.year + 1, month=2, day=1) - timedelta(days=1)
            else:
                next_month = today.month + 1
                if next_month > 12:
                    end_date = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
                else:
                    end_date = today.replace(month=next_month + 1, day=1) - timedelta(days=1)
        
        Project = self.env["project.project"]
        
        # Check if x_event_date field exists
        if "x_event_date" not in Project._fields:
            return []
        
        domain = [
            ("x_event_date", ">=", start_date),
            ("x_event_date", "<=", end_date),
        ]
        projects = Project.search(domain, order="x_event_date asc")
        
        # Define status colors based on CRM stage
        stage_colors = {
            "New": "#87CEEB",          # Light Blue
            "Qualified": "#87CEEB",     # Light Blue
            "Awaiting Deposit": "#FFD700",  # Yellow
            "Proposition": "#FFD700",   # Yellow
            "Booked": "#28A745",        # Green
            "Won": "#28A745",           # Green
            "Planning": "#FFA500",      # Orange
            "Completed": "#6C757D",     # Gray
        }
        default_color = "#17A2B8"  # Teal for unknown stages
        
        result = []
        for project in projects:
            # Get CRM lead stage for color
            stage_name = ""
            color = default_color
            crm_lead_id = None
            
            if hasattr(project, 'x_crm_lead_id') and project.x_crm_lead_id:
                lead = project.x_crm_lead_id
                crm_lead_id = lead.id
                if lead.stage_id:
                    stage_name = lead.stage_id.name
                    color = stage_colors.get(stage_name, default_color)
            
            event_data = {
                "id": project.id,
                "name": project.name,
                "event_date": project.x_event_date.isoformat() if project.x_event_date else False,
                "partner_name": project.partner_id.name if project.partner_id else "",
                "stage_name": stage_name,
                "color": color,
                "crm_lead_id": crm_lead_id,
                # Action metadata
                "action": {
                    "type": "ir.actions.act_window",
                    "res_model": "project.project",
                    "res_id": project.id,
                    "views": [[False, "form"]],
                    "target": "current",
                },
                "crm_action": {
                    "type": "ir.actions.act_window",
                    "res_model": "crm.lead",
                    "res_id": crm_lead_id,
                    "views": [[False, "form"]],
                    "target": "current",
                } if crm_lead_id else None,
            }
            result.append(event_data)
        
        return result
    
    @api.model
    def get_sales_kpis(self):
        """Get sales KPIs for the Sales Dashboard.
        
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

