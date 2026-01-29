# Part of Party Time Texas. See LICENSE file for full copyright and licensing details.
"""
HTTP Controllers for PTT Project Dashboard.

Based on: Cybrosys project_dashboard_odoo/controllers/project_dashboard_odoo.py

Provides JSON-RPC endpoints for the Project Dashboard inside the Projects app.

Enhanced Features (v2.1.0):
- Saved filter presets (CRUD)
- Quick task assignment
- Excel export functionality
"""

import io
import json
import random
from datetime import datetime, time

import pytz
from odoo import http, fields
from odoo.http import request


class PTTDashboardController(http.Controller):
    """HTTP Controller for Project Dashboard data."""

    @staticmethod
    def _as_date(value, record=None):
        """Normalize date/datetime values to a user-context date.

        In Odoo 19, `project.task.date_deadline` is a Datetime (UTC). For dashboard
        logic like "overdue today", we must compare dates, not datetimes, and we
        should respect the user's timezone.

        Args:
            value: Date, datetime, or string value to convert
            record: A recordset (e.g., request.env.user) for timezone context.
                    Odoo 19's context_timestamp() requires a BaseModel, not Environment.
        """
        if not value:
            return False
        # Convert to datetime first (handles strings, date, datetime)
        dt_utc = fields.Datetime.to_datetime(value)
        if not dt_utc:
            return False

        # If a recordset is provided, convert UTC -> user's timezone before taking date
        # Odoo 19: context_timestamp(record: BaseModel, timestamp: datetime)
        if record is not None:
            dt_local = fields.Datetime.context_timestamp(record, dt_utc)
            return dt_local.date()

        # Fallback: best-effort without user context
        return dt_utc.date()

    @staticmethod
    def _day_bounds_utc(env, day):
        """Return (start_utc, end_utc) for a given date in the user's timezone."""
        tz = pytz.timezone(env.user.tz or "UTC")
        start_local = tz.localize(datetime.combine(day, time.min))
        end_local = tz.localize(datetime.combine(day, time.max))
        start_utc = start_local.astimezone(pytz.UTC).replace(tzinfo=None)
        end_utc = end_local.astimezone(pytz.UTC).replace(tzinfo=None)
        return start_utc, end_utc

    def _get_random_color(self):
        """Generate a random hex color for charts."""
        return "#{:06x}".format(random.randint(0, 0xFFFFFF))

    def _get_filter_domain(self, filters, model='task', include_dates=True, env=None):
        """Build domain from filter parameters.
        
        Args:
            filters: dict with user, customer, project, start_date, end_date
            model: 'task' or 'project' to determine field names
            include_dates: whether to include date filters (default True)
            env: Odoo environment to use for timezone-aware datetime bounds
            
        Returns:
            list: Odoo domain
            
        Note:
            - Tasks use 'date_deadline' for date filtering
            - Projects use 'ptt_event_date' for date filtering
        """
        domain = []
        if not filters:
            return domain

        env = env or request.env
            
        user_id = filters.get('user')
        customer_id = filters.get('customer')
        project_id = filters.get('project')
        start_date = filters.get('start_date')
        end_date = filters.get('end_date')
        
        if project_id and project_id != 'null':
            if model == 'task':
                domain.append(('project_id', '=', int(project_id)))
            else:
                domain.append(('id', '=', int(project_id)))
                
        if user_id and user_id != 'null' and user_id != '':
            # Handle "me" special value
            if user_id == 'me':
                user_id = request.env.uid
            else:
                user_id = int(user_id)
            if model == 'task':
                # Match tasks the user is assigned to OR manages via project
                domain.append('|')
                domain.append(('user_ids', 'in', [user_id]))
                domain.append(('project_id.user_id', '=', user_id))
            else:
                domain.append(('user_id', '=', user_id))
        
        # Date filters - use appropriate field based on model
        if include_dates:
            if model == 'task':
                # Tasks use date_deadline (Datetime in Odoo 19) - apply TZ-safe bounds
                if start_date and start_date != 'null':
                    start_day = fields.Date.to_date(start_date)
                    start_utc, _ = self._day_bounds_utc(env, start_day)
                    domain.append(('date_deadline', '>=', start_utc))
                if end_date and end_date != 'null':
                    end_day = fields.Date.to_date(end_date)
                    _, end_utc = self._day_bounds_utc(env, end_day)
                    domain.append(('date_deadline', '<=', end_utc))
            else:
                # Projects use ptt_event_date (event date from CRM)
                if start_date and start_date != 'null':
                    domain.append(('ptt_event_date', '>=', start_date))
                if end_date and end_date != 'null':
                    domain.append(('ptt_event_date', '<=', end_date))
            
        return domain

    # =========================================================================
    # NEW v2.3.0 ENDPOINTS - Focused Dashboard
    # =========================================================================
    # SALES KPIs
    # =========================================================================

    @http.route('/ptt/dashboard/sales-kpis', auth='user', type='jsonrpc')
    def get_sales_kpis(self, filters=None):
        """Get sales KPIs: Total confirmed SO revenue and top sales rep."""
        SaleOrder = request.env['sale.order']
        
        # Build domain for confirmed orders
        domain = [('state', '=', 'sale')]
        
        # Apply date filters if provided
        if filters:
            start_date = filters.get('start_date')
            end_date = filters.get('end_date')
            if start_date:
                domain.append(('date_order', '>=', start_date))
            if end_date:
                domain.append(('date_order', '<=', end_date))
        
        orders = SaleOrder.search(domain)
        total = sum(orders.mapped('amount_total'))
        
        # Format as currency string (no decimals for large numbers)
        if total >= 1000:
            formatted = f"{total:,.0f}"
        else:
            formatted = f"{total:,.2f}"
        
        # Find top sales rep
        sales_by_user = {}
        for order in orders:
            user = order.user_id
            if user:
                if user.id not in sales_by_user:
                    sales_by_user[user.id] = {'name': user.name, 'total': 0}
                sales_by_user[user.id]['total'] += order.amount_total
        
        top_rep = ''
        top_amount = '0'
        if sales_by_user:
            top = max(sales_by_user.values(), key=lambda x: x['total'])
            top_rep = top['name']
            if top['total'] >= 1000:
                top_amount = f"{top['total']:,.0f}"
            else:
                top_amount = f"{top['total']:,.2f}"
        
        return {
            'total_revenue': formatted,
            'confirmed_so_ids': orders.ids,
            'top_sales_rep': top_rep,
            'top_sales_amount': top_amount,
        }

    @http.route('/ptt/dashboard/sales-by-rep', auth='user', type='jsonrpc')
    def get_sales_by_rep(self, filters=None):
        """Get sales totals grouped by salesperson for bar chart."""
        SaleOrder = request.env['sale.order']
        
        # Build domain for confirmed orders
        domain = [('state', '=', 'sale')]
        
        # Apply date filters if provided
        if filters:
            start_date = filters.get('start_date')
            end_date = filters.get('end_date')
            if start_date:
                domain.append(('date_order', '>=', start_date))
            if end_date:
                domain.append(('date_order', '<=', end_date))
        
        orders = SaleOrder.search(domain)
        
        # Group by user
        sales_by_user = {}
        for order in orders:
            user = order.user_id
            if user:
                if user.id not in sales_by_user:
                    sales_by_user[user.id] = {
                        'name': user.name,
                        'total': 0,
                    }
                sales_by_user[user.id]['total'] += order.amount_total
        
        # Sort by total descending
        sorted_sales = sorted(sales_by_user.values(), key=lambda x: x['total'], reverse=True)
        
        labels = [s['name'] for s in sorted_sales]
        data = [round(s['total'], 2) for s in sorted_sales]
        
        return {
            'labels': labels,
            'data': data,
        }

    # =========================================================================

    @http.route('/ptt/dashboard/kpis', auth='user', type='jsonrpc')
    def get_kpis(self, filters=None):
        """Get focused KPI data: My Tasks, My Projects, Overdue, Due This Week."""
        today = fields.Date.context_today(request.env.user)
        uid = request.env.uid
        Project = request.env['project.project']
        Task = request.env['project.task']

        # Apply filters
        filter_domain = self._get_filter_domain(filters or {}, model='task', env=request.env)
        
        # My Tasks (assigned to current user, not done)
        my_tasks_domain = [('user_ids', 'in', [uid]), ('stage_id.fold', '=', False)] + filter_domain
        my_tasks = Task.search(my_tasks_domain)
        
        # My Projects (user is manager or follower)
        my_projects = Project.search([
            '|',
            ('user_id', '=', uid),
            ('message_partner_ids', 'in', [request.env.user.partner_id.id]),
        ])

        # My Activities (pending activities assigned to current user)
        Activity = request.env['mail.activity']
        my_activities = Activity.search_count([('user_id', '=', uid)])

        # My Overdue Tasks
        my_overdue = my_tasks.filtered(
            lambda t: t.date_deadline and self._as_date(t.date_deadline, request.env.user) < today
        )
        
        # Due This Week (tasks due within 7 days)
        from datetime import timedelta
        week_end = today + timedelta(days=7)
        due_this_week = my_tasks.filtered(
            lambda t: t.date_deadline
            and today <= self._as_date(t.date_deadline, request.env.user) <= week_end
        )

        # Unassigned Tasks (no users assigned, not done)
        unassigned_tasks = Task.search([
            ('user_ids', '=', False),
            ('stage_id.fold', '=', False),
        ] + filter_domain)

        # Tasks with No Due Date (not done)
        no_due_date_tasks = Task.search([
            ('date_deadline', '=', False),
            ('stage_id.fold', '=', False),
        ] + filter_domain)

        return {
            'my_tasks': len(my_tasks),
            'my_tasks_ids': my_tasks.ids,
            'my_projects': len(my_projects),
            'my_projects_ids': my_projects.ids,
            'my_activities': my_activities,
            'my_overdue_tasks': len(my_overdue),
            'my_overdue_tasks_ids': my_overdue.ids,
            'unassigned_tasks': len(unassigned_tasks),
            'unassigned_tasks_ids': unassigned_tasks.ids,
            'no_due_date_tasks': len(no_due_date_tasks),
            'no_due_date_tasks_ids': no_due_date_tasks.ids,
        }

    @http.route('/ptt/dashboard/my-projects', auth='user', type='jsonrpc')
    def get_my_projects(self, page=1, limit=5, filters=None):
        """Get paginated list of user's projects with task counts."""
        uid = request.env.uid
        Project = request.env['project.project']
        Task = request.env['project.task']
        
        # Projects where user is manager or follower
        domain = [
            '|',
            ('user_id', '=', uid),
            ('message_partner_ids', 'in', [request.env.user.partner_id.id]),
        ]
        
        # Apply customer/project filters if provided
        if filters:
            if filters.get('customer') and filters['customer'] != '':
                domain.append(('partner_id', '=', int(filters['customer'])))
            if filters.get('project') and filters['project'] != '':
                domain.append(('id', '=', int(filters['project'])))
        
        total_count = Project.search_count(domain)
        offset = (page - 1) * limit
        projects = Project.search(domain, limit=limit, offset=offset, order='is_favorite desc, name asc')
        
        project_list = []
        for proj in projects:
            # Count active tasks in this project
            task_count = Task.search_count([
                ('project_id', '=', proj.id),
                ('stage_id.fold', '=', False),
            ])
            project_list.append({
                'id': proj.id,
                'name': proj.name,
                'partner_name': proj.partner_id.name if proj.partner_id else None,
                'task_count': task_count,
                'is_favorite': proj.is_favorite,
                'user_id': proj.user_id.id if proj.user_id else None,
                'user_name': proj.user_id.name if proj.user_id else None,
            })
        
        return {
            'projects': project_list,
            'total': total_count,
            'page': page,
            'pages': max(1, (total_count + limit - 1) // limit),
        }

    @http.route('/ptt/dashboard/events', auth='user', type='jsonrpc')
    def get_events(self, start_date=None, end_date=None):
        """Get events from CRM and Projects for a date range (defaults to current month)."""
        from datetime import timedelta
        
        today = fields.Date.context_today(request.env.user)
        CrmLead = request.env['crm.lead']
        Project = request.env['project.project']

        # Parse date range or default to current month
        if start_date:
            start = fields.Date.from_string(start_date)
        else:
            start = today.replace(day=1)
        
        if end_date:
            end = fields.Date.from_string(end_date)
        else:
            # Last day of current month
            if today.month == 12:
                end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)

        events = []

        # Status mapping for CRM stages
        # Lead stages: New, Qualified = "lead"
        # Quote sent stages = "quote"
        # Won/Booked = "booked"

        leads = CrmLead.search([
            ('ptt_event_date', '>=', start),
            ('ptt_event_date', '<=', end),
        ], order='ptt_event_date asc')
        
        for lead in leads:
            event_date = lead.ptt_event_date
            if event_date:
                # Determine status based on stage
                stage_name = (lead.stage_id.name or '').lower()
                if 'won' in stage_name or 'book' in stage_name:
                    status = 'booked'
                    status_label = 'Booked'
                elif 'quote' in stage_name or 'proposal' in stage_name or 'sent' in stage_name:
                    status = 'quote'
                    status_label = 'Quote Sent'
                else:
                    status = 'lead'
                    status_label = 'Lead'
                
                events.append({
                    'id': lead.id,
                    'model': 'crm.lead',
                    'name': lead.name or 'Untitled Event',
                    'customer': lead.partner_id.name if lead.partner_id else None,
                    'date': str(event_date),
                    'month': event_date.strftime('%b').upper(),
                    'day': event_date.strftime('%d'),
                    'status': status,
                    'status_label': status_label,
                })
        
        # Get Projects with event dates in the date range
        projects = Project.search([
            ('ptt_event_date', '>=', start),
            ('ptt_event_date', '<=', end),
        ], order='ptt_event_date asc')
        
        for proj in projects:
            event_date = proj.ptt_event_date
            if event_date:
                events.append({
                    'id': proj.id,
                    'model': 'project.project',
                    'name': proj.name or 'Untitled Project',
                    'customer': proj.partner_id.name if proj.partner_id else None,
                    'date': str(event_date),
                    'month': event_date.strftime('%b').upper(),
                    'day': event_date.strftime('%d'),
                    'status': 'booked',
                    'status_label': 'Project',
                })
        
        # Sort all events by date
        events.sort(key=lambda x: x['date'])

        return {'events': events}  # Return all events in 14-day window

    @http.route('/ptt/dashboard/my-tasks', auth='user', type='jsonrpc')
    def get_my_tasks(self, page=1, limit=5, filters=None):
        """Get paginated list of tasks assigned to current user."""
        today = fields.Date.context_today(request.env.user)
        uid = request.env.uid
        Task = request.env['project.task']
        
        # Tasks assigned to current user, not done
        domain = [
            ('user_ids', 'in', [uid]),
            ('stage_id.fold', '=', False),
        ]
        
        # Apply filters
        domain.extend(self._get_filter_domain(filters or {}, model='task', env=request.env))
        
        total_count = Task.search_count(domain)
        offset = (page - 1) * limit
        
        # Order: overdue first, then by deadline
        tasks = Task.search(domain, limit=limit, offset=offset, order='date_deadline asc nulls last')
        
        task_list = []
        for task in tasks:
            deadline_date = self._as_date(task.date_deadline, request.env.user) if task.date_deadline else None
            is_overdue = deadline_date and deadline_date < today
            
            if deadline_date:
                delta = (today - deadline_date).days
                if delta > 0:
                    deadline_display = f"{delta}d overdue"
                elif delta == 0:
                    deadline_display = "Today"
                else:
                    deadline_display = f"In {abs(delta)}d"
            else:
                deadline_display = None
            
            task_list.append({
                'id': task.id,
                'name': task.name,
                'project_id': task.project_id.id if task.project_id else None,
                'project_name': task.project_id.name if task.project_id else '',
                'deadline_display': deadline_display,
                'is_overdue': is_overdue,
                'priority': task.priority,
                'stage_name': task.stage_id.name if task.stage_id else '',
            })
        
        return {
            'tasks': task_list,
            'total': total_count,
            'page': page,
            'pages': max(1, (total_count + limit - 1) // limit),
        }

    # =========================================================================
    # LEGACY ENDPOINTS (kept for backward compatibility)
    # =========================================================================

    @http.route('/ptt/dashboard/tiles', auth='user', type='jsonrpc')
    def get_tiles_data(self):
        """Get main tile/KPI data for dashboard.

        Returns tile counts like: My Tasks, Total Projects, Active Tasks,
        My Overdue Tasks, Overdue Tasks, Today Tasks
        """
        today = fields.Date.context_today(request.env.user)
        uid = request.env.uid
        Project = request.env['project.project']
        Task = request.env['project.task']

        is_manager = request.env.user.has_group('project.group_project_manager')

        if is_manager:
            # Manager sees all projects/tasks
            all_projects = Project.search([])
            all_tasks = Task.search([])
        else:
            # Regular user sees their assigned projects/tasks
            all_projects = Project.search([
                '|',
                ('user_id', '=', uid),
                ('message_partner_ids', 'in', [request.env.user.partner_id.id]),
            ])
            all_tasks = Task.search([('user_ids', 'in', [uid])])

        # Active tasks (not done/canceled)
        active_tasks = all_tasks.filtered(lambda t: not t.stage_id.fold)

        # My tasks
        my_tasks = Task.search([('user_ids', 'in', [uid])])

        # My overdue tasks
        my_overdue = my_tasks.filtered(
            lambda t: t.date_deadline and self._as_date(t.date_deadline, request.env.user) < today
            and not t.stage_id.fold
        )

        # All overdue tasks (visible to user)
        all_overdue = all_tasks.filtered(
            lambda t: t.date_deadline and self._as_date(t.date_deadline, request.env.user) < today
            and not t.stage_id.fold
        )

        # Today's tasks
        today_tasks = all_tasks.filtered(
            lambda t: t.date_deadline and self._as_date(t.date_deadline, request.env.user) == today
            and not t.stage_id.fold
        )

        # Get user avatar URL - Odoo handles default avatars automatically
        user = request.env.user
        # Always provide the avatar URL - Odoo returns default avatar if none set
        user_avatar = f'/web/image/res.users/{user.id}/avatar_128?unique={user.write_date}'

        return {
            'my_tasks': len(my_tasks),
            'my_tasks_ids': my_tasks.ids,
            'total_projects': len(all_projects),
            'total_projects_ids': all_projects.ids,
            'active_tasks': len(active_tasks),
            'active_tasks_ids': active_tasks.ids,
            'my_overdue_tasks': len(my_overdue),
            'my_overdue_tasks_ids': my_overdue.ids,
            'overdue_tasks': len(all_overdue),
            'overdue_tasks_ids': all_overdue.ids,
            'today_tasks': len(today_tasks),
            'today_tasks_ids': today_tasks.ids,
            'is_manager': is_manager,
            'user_name': user.name,
            'user_avatar': user_avatar,
        }

    @http.route('/ptt/dashboard/tasks', auth='user', type='jsonrpc')
    def get_all_tasks(self, page=1, limit=5, filters=None):
        """Get paginated task list for the All Tasks table.

        Returns tasks with: name, project, deadline, priority, stage, id
        """
        today = fields.Date.context_today(request.env.user)
        uid = request.env.uid
        Task = request.env['project.task']

        is_manager = request.env.user.has_group('project.group_project_manager')

        # Get tasks with deadlines, prioritize overdue
        if is_manager:
            domain = [('date_deadline', '!=', False)]
        else:
            domain = [('user_ids', 'in', [uid]), ('date_deadline', '!=', False)]

        # Exclude done/canceled
        domain.append(('stage_id.fold', '=', False))
        
        # Apply filters
        domain.extend(self._get_filter_domain(filters, model='task', env=request.env))

        total_count = Task.search_count(domain)
        offset = (page - 1) * limit

        tasks = Task.search(domain, order='date_deadline asc', limit=limit, offset=offset)

        task_list = []
        for task in tasks:
            # Calculate days ago/until
            if task.date_deadline:
                deadline_date = self._as_date(task.date_deadline, request.env.user)
                delta = (today - deadline_date).days
                if delta > 0:
                    deadline_display = f"{delta} days ago"
                    deadline_class = "overdue"
                elif delta == 0:
                    deadline_display = "Today"
                    deadline_class = "today"
                else:
                    deadline_display = f"In {abs(delta)} days"
                    deadline_class = "upcoming"
            else:
                deadline_display = ""
                deadline_class = ""

            task_list.append({
                'id': task.id,
                'name': task.name,
                'project_id': task.project_id.id if task.project_id else False,
                'project_name': task.project_id.name if task.project_id else '',
                'deadline': str(task.date_deadline) if task.date_deadline else '',
                'deadline_display': deadline_display,
                'deadline_class': deadline_class,
                'priority': task.priority,
                'stage_id': task.stage_id.id if task.stage_id else False,
                'stage_name': task.stage_id.name if task.stage_id else '',
            })

        return {
            'tasks': task_list,
            'total': total_count,
            'page': page,
            'pages': max(1, (total_count + limit - 1) // limit),
        }

    @http.route('/ptt/dashboard/task-deadline-chart', auth='user', type='jsonrpc')
    def get_task_deadline_chart(self, filters=None):
        """Get data for Task Deadline pie chart (Overdue/Today/Upcoming)."""
        today = fields.Date.context_today(request.env.user)
        uid = request.env.uid
        Task = request.env['project.task']

        is_manager = request.env.user.has_group('project.group_project_manager')

        if is_manager:
            base_domain = [('stage_id.fold', '=', False)]
        else:
            base_domain = [('user_ids', 'in', [uid]), ('stage_id.fold', '=', False)]

        # Apply filters (excluding date filters for this chart - it groups by deadline)
        filter_domain = self._get_filter_domain(filters, model='task', env=request.env)
        # Remove date filters as they conflict with this chart's purpose
        filter_domain = [d for d in filter_domain if d[0] != 'date_deadline']
        base_domain.extend(filter_domain)

        # date_deadline is Datetime (UTC): count using TZ-safe day bounds
        base_domain = base_domain + [('date_deadline', '!=', False)]
        start_utc, end_utc = self._day_bounds_utc(request.env, today)
        overdue = Task.search_count(base_domain + [('date_deadline', '<', start_utc)])
        today_count = Task.search_count(
            base_domain + [('date_deadline', '>=', start_utc), ('date_deadline', '<=', end_utc)]
        )
        upcoming = Task.search_count(base_domain + [('date_deadline', '>', end_utc)])

        return {
            'labels': ['Overdue', 'Today', 'Upcoming'],
            'data': [overdue, today_count, upcoming],
            'colors': ['#95a5a6', '#f1c40f', '#9b59b6'],  # Gray, Yellow, Purple
        }

    @http.route('/ptt/dashboard/task-stages-chart', auth='user', type='jsonrpc')
    def get_task_stages_chart(self, filters=None):
        """Get data for Task By Stages doughnut chart."""
        uid = request.env.uid
        Task = request.env['project.task']
        Stage = request.env['project.task.type']

        is_manager = request.env.user.has_group('project.group_project_manager')

        if is_manager:
            base_domain = []
        else:
            base_domain = [('user_ids', 'in', [uid])]

        # Apply filters
        base_domain.extend(self._get_filter_domain(filters, model='task', env=request.env))

        stages = Stage.search([])

        labels = []
        data = []
        colors = ['#e74c3c', '#2ecc71', '#3498db', '#9b59b6', '#f39c12', '#1abc9c']

        for stage in stages:
            count = Task.search_count(base_domain + [('stage_id', '=', stage.id)])
            if count > 0:
                labels.append(stage.name)
                data.append(count)

        return {
            'labels': labels,
            'data': data,
            'colors': colors[:len(labels)],
        }

    @http.route('/ptt/dashboard/projects-chart', auth='user', type='jsonrpc')
    def get_projects_chart(self, filters=None):
        """Get data for Projects by Status doughnut chart."""
        uid = request.env.uid
        Project = request.env['project.project']

        is_manager = request.env.user.has_group('project.group_project_manager')

        if is_manager:
            base_domain = [('active', '=', True)]
        else:
            base_domain = [('active', '=', True), '|', ('user_id', '=', uid), ('message_partner_ids', 'in', [request.env.user.partner_id.id])]

        # Define status categories based on task counts and stage
        labels = []
        data = []

        projects = Project.search(base_domain)

        # Group by simple status categories
        active_count = 0
        completed_count = 0
        on_hold_count = 0

        for project in projects:
            # Check task completion
            total_tasks = len(project.task_ids)
            if total_tasks == 0:
                on_hold_count += 1
            else:
                done_tasks = len(project.task_ids.filtered(lambda t: t.stage_id.fold))
                if done_tasks == total_tasks:
                    completed_count += 1
                else:
                    active_count += 1

        if active_count > 0:
            labels.append('Active')
            data.append(active_count)
        if completed_count > 0:
            labels.append('Completed')
            data.append(completed_count)
        if on_hold_count > 0:
            labels.append('No Tasks')
            data.append(on_hold_count)

        return {
            'labels': labels,
            'data': data,
        }

    @http.route('/ptt/dashboard/task-project-chart', auth='user', type='jsonrpc')
    def get_task_project_chart(self, filters=None):
        """Get data for Task By Project bar chart.
        
        Shows task counts per project. Date filters apply to tasks (by deadline),
        not to projects, so we can show projects that have tasks in the date range.
        """
        uid = request.env.uid
        Project = request.env['project.project']
        Task = request.env['project.task']

        is_manager = request.env.user.has_group('project.group_project_manager')

        # Build project domain - exclude dates (dates filter tasks, not projects)
        project_domain = self._get_filter_domain(filters, model='project', include_dates=False, env=request.env)
        
        if is_manager:
            projects = Project.search(project_domain, limit=10, order='create_date desc')
        else:
            base_domain = [
                '|',
                ('user_id', '=', uid),
                ('message_partner_ids', 'in', [request.env.user.partner_id.id]),
            ]
            projects = Project.search(base_domain + project_domain, limit=10, order='create_date desc')

        # Build task domain from filters
        task_filter_domain = self._get_filter_domain(filters, model='task', env=request.env)

        labels = []
        data = []
        colors = ['#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6', '#1abc9c']

        for project in projects:
            task_domain = [('project_id', '=', project.id)] + task_filter_domain
            task_count = Task.search_count(task_domain)
            if task_count > 0:
                labels.append(project.name[:15] + '...' if len(project.name) > 15 else project.name)
                data.append(task_count)

        return {
            'labels': labels,
            'data': data,
            'colors': colors[:len(labels)],
        }

    @http.route('/ptt/dashboard/priority-chart', auth='user', type='jsonrpc')
    def get_priority_chart(self, filters=None):
        """Get data for Priority Wise bar chart.
        
        Odoo 19 priority levels:
        - '0' = Low priority
        - '1' = Medium priority
        - '2' = High priority
        - '3' = Urgent
        """
        uid = request.env.uid
        Task = request.env['project.task']

        is_manager = request.env.user.has_group('project.group_project_manager')

        if is_manager:
            base_domain = [('stage_id.fold', '=', False)]
        else:
            base_domain = [('user_ids', 'in', [uid]), ('stage_id.fold', '=', False)]

        # Apply filters
        base_domain.extend(self._get_filter_domain(filters, model='task', env=request.env))

        # Odoo 19 has 4 priority levels
        low = Task.search_count(base_domain + [('priority', '=', '0')])
        medium = Task.search_count(base_domain + [('priority', '=', '1')])
        high = Task.search_count(base_domain + [('priority', '=', '2')])
        urgent = Task.search_count(base_domain + [('priority', '=', '3')])

        return {
            'labels': ['Low', 'Medium', 'High', 'Urgent'],
            'data': [low, medium, high, urgent],
            'colors': ['#93c5fd', '#fcd34d', '#f97316', '#ef4444'],  # Blue, Yellow, Orange, Red
        }

    @http.route('/ptt/dashboard/activities', auth='user', type='jsonrpc')
    def get_activities(self, page=1, limit=5, filters=None):
        """Get paginated activities list.
        
        Shows activities for both project.task and project.project records.
        When filters are applied, includes activities from:
        - Tasks matching the filter criteria
        - Projects matching the filter criteria (manager, customer, project)
        """
        uid = request.env.uid
        Activity = request.env['mail.activity']
        Task = request.env['project.task']
        Project = request.env['project.project']

        domain = [
            ('user_id', '=', uid),
            ('res_model', 'in', ['project.task', 'project.project']),
        ]

        # If filters are applied, get filtered task AND project IDs
        if filters:
            task_filter_domain = self._get_filter_domain(filters, model='task')
            project_filter_domain = self._get_filter_domain(filters, model='project', env=request.env)
            
            # Only apply filtering if we have actual filter criteria
            if task_filter_domain or project_filter_domain:
                filtered_task_ids = []
                filtered_project_ids = []
                
                # Get filtered tasks
                if task_filter_domain:
                    filtered_tasks = Task.search(task_filter_domain)
                    filtered_task_ids = filtered_tasks.ids
                
                # Get filtered projects (for project-level activities)
                if project_filter_domain:
                    filtered_projects = Project.search(project_filter_domain)
                    filtered_project_ids = filtered_projects.ids
                elif task_filter_domain:
                    # If only task filters, get projects from those tasks
                    filtered_tasks = Task.search(task_filter_domain)
                    filtered_project_ids = filtered_tasks.mapped('project_id').ids
                
                # Build OR domain to include both task and project activities
                if filtered_task_ids or filtered_project_ids:
                    # Remove the generic res_model filter
                    domain = [d for d in domain if d != ('res_model', 'in', ['project.task', 'project.project'])]
                    
                    # Build OR condition for activities
                    activity_conditions = []
                    if filtered_task_ids:
                        activity_conditions.append('&')
                        activity_conditions.append(('res_model', '=', 'project.task'))
                        activity_conditions.append(('res_id', 'in', filtered_task_ids))
                    if filtered_project_ids:
                        activity_conditions.append('&')
                        activity_conditions.append(('res_model', '=', 'project.project'))
                        activity_conditions.append(('res_id', 'in', filtered_project_ids))
                    
                    # Combine with OR if we have both
                    if filtered_task_ids and filtered_project_ids:
                        domain.append('|')
                    domain.extend(activity_conditions)

        total_count = Activity.search_count(domain)
        offset = (page - 1) * limit

        activities = Activity.search(domain, order='date_deadline asc', limit=limit, offset=offset)

        activity_list = []
        for act in activities:
            activity_list.append({
                'id': act.id,
                'res_id': act.res_id,
                'res_model': act.res_model,
                'task_name': act.res_name or '',
                'activity_type': act.activity_type_id.name if act.activity_type_id else '',
                'summary': act.summary or '',
                'date': str(act.date_deadline) if act.date_deadline else '',
            })

        return {
            'activities': activity_list,
            'total': total_count,
            'page': page,
            'pages': max(1, (total_count + limit - 1) // limit),
        }

    @http.route('/ptt/dashboard/filter', auth='user', type='jsonrpc')
    def get_filter_options(self):
        """Get filter dropdown options (users, projects)."""
        User = request.env['res.users']
        Project = request.env['project.project']

        # Get internal active users (exclude portal/share)
        users = User.search([('share', '=', False), ('active', '=', True)])
        user_list = [{'id': u.id, 'name': u.name} for u in users]

        # Get projects
        projects = Project.search([('active', '=', True)])
        project_list = [{'id': p.id, 'name': p.name} for p in projects]

        return {
            'users': user_list,
            'projects': project_list,
        }

    @http.route('/ptt/dashboard/filter-apply', auth='user', type='jsonrpc')
    def apply_filter(self, **kw):
        """Apply filters and return filtered data.
        
        Reuses _get_filter_domain() to build domains consistently (DRY principle).
        """
        data = kw.get('data', {})
        
        today = fields.Date.context_today(request.env.user)
        uid = request.env.uid
        Task = request.env['project.task']
        Project = request.env['project.project']

        # Build domains using shared helper method (DRY)
        # Projects: filter by user, customer, project - no date filter on projects here
        project_domain = self._get_filter_domain(data, model='project', include_dates=False, env=request.env)
        filtered_projects = Project.search(project_domain) if project_domain else Project.search([])

        # Tasks: filter by date, and limit to filtered projects
        task_domain = self._get_filter_domain(data, model='task', include_dates=True, env=request.env)
        if filtered_projects:
            task_domain.append(('project_id', 'in', filtered_projects.ids))

        # Get filtered tasks
        all_tasks = Task.search(task_domain) if task_domain else Task.search([])
        active_tasks = all_tasks.filtered(lambda t: not t.stage_id.fold)
        my_tasks = all_tasks.filtered(lambda t: uid in t.user_ids.ids)
        my_overdue = my_tasks.filtered(
            lambda t: t.date_deadline and self._as_date(t.date_deadline, request.env.user) < today
            and not t.stage_id.fold
        )
        all_overdue = all_tasks.filtered(
            lambda t: t.date_deadline and self._as_date(t.date_deadline, request.env.user) < today
            and not t.stage_id.fold
        )
        today_tasks = all_tasks.filtered(
            lambda t: t.date_deadline and self._as_date(t.date_deadline, request.env.user) == today
            and not t.stage_id.fold
        )

        return {
            'my_tasks': len(my_tasks),
            'my_tasks_ids': my_tasks.ids,
            'total_projects': len(filtered_projects),
            'total_projects_ids': filtered_projects.ids,
            'active_tasks': len(active_tasks),
            'active_tasks_ids': active_tasks.ids,
            'my_overdue_tasks': len(my_overdue),
            'my_overdue_tasks_ids': my_overdue.ids,
            'overdue_tasks': len(all_overdue),
            'overdue_tasks_ids': all_overdue.ids,
            'today_tasks': len(today_tasks),
            'today_tasks_ids': today_tasks.ids,
        }

    # =========================================================================
    # SAVED FILTER PRESETS
    # =========================================================================

    @http.route('/ptt/dashboard/presets', auth='user', type='jsonrpc')
    def get_presets(self):
        """Get all saved filter presets for the current user."""
        Preset = request.env['ptt.dashboard.filter.preset']
        presets = Preset.search([('user_id', '=', request.env.uid)])
        
        return {
            'presets': [
                {'id': p.id, 'name': p.name}
                for p in presets
            ]
        }

    @http.route('/ptt/dashboard/save-preset', auth='user', type='jsonrpc')
    def save_preset(self, name, filters):
        """Save current filter combination as a new preset."""
        try:
            Preset = request.env['ptt.dashboard.filter.preset']
            preset = Preset.create({
                'name': name,
                'user_id': request.env.uid,
                'filters_json': json.dumps(filters),
            })
            return {'success': True, 'id': preset.id}
        except (ValueError, TypeError) as e:
            return {'success': False, 'error': f'Invalid data: {e}'}
        except Exception as e:  # noqa: BLE001 - catch-all for unexpected DB errors
            return {'success': False, 'error': str(e)}

    @http.route('/ptt/dashboard/load-preset', auth='user', type='jsonrpc')
    def load_preset(self, preset_id):
        """Load a saved filter preset."""
        try:
            Preset = request.env['ptt.dashboard.filter.preset']
            preset = Preset.browse(int(preset_id))
            
            if not preset.exists() or preset.user_id.id != request.env.uid:
                return {'success': False, 'error': 'Preset not found'}
            
            return {
                'success': True,
                'name': preset.name,
                'filters': preset.get_filters(),
            }
        except (ValueError, TypeError) as e:
            return {'success': False, 'error': f'Invalid preset ID: {e}'}
        except Exception as e:  # noqa: BLE001 - catch-all for unexpected errors
            return {'success': False, 'error': str(e)}

    @http.route('/ptt/dashboard/delete-preset', auth='user', type='jsonrpc')
    def delete_preset(self, preset_id):
        """Delete a saved filter preset."""
        try:
            Preset = request.env['ptt.dashboard.filter.preset']
            preset = Preset.browse(int(preset_id))
            
            if not preset.exists() or preset.user_id.id != request.env.uid:
                return {'success': False, 'error': 'Preset not found'}
            
            preset.unlink()
            return {'success': True}
        except (ValueError, TypeError) as e:
            return {'success': False, 'error': f'Invalid preset ID: {e}'}
        except Exception as e:  # noqa: BLE001 - catch-all for unexpected errors
            return {'success': False, 'error': str(e)}

    # =========================================================================
    # QUICK TASK ASSIGNMENT
    # =========================================================================

    @http.route('/ptt/dashboard/assign-task', auth='user', type='jsonrpc')
    def assign_task(self, task_id, user_id):
        """Assign a task to a user directly from the dashboard."""
        try:
            Task = request.env['project.task']
            User = request.env['res.users']
            
            task = Task.browse(int(task_id))
            user = User.browse(int(user_id))
            
            if not task.exists():
                return {'success': False, 'error': 'Task not found'}
            if not user.exists():
                return {'success': False, 'error': 'User not found'}
            
            # Add user to task's assignees
            task.write({'user_ids': [(4, user.id)]})
            
            return {'success': True, 'task_name': task.name, 'user_name': user.name}
        except (ValueError, TypeError) as e:
            return {'success': False, 'error': f'Invalid ID: {e}'}
        except Exception as e:  # noqa: BLE001 - catch-all for unexpected errors
            return {'success': False, 'error': str(e)}

    # =========================================================================
    # EXCEL EXPORT
    # =========================================================================

    @http.route('/ptt/dashboard/export', auth='user', type='http')
    def export_dashboard(self, **kw):
        """Export dashboard data to Excel file."""
        try:
            # Try to import xlsxwriter (standard in Odoo)
            import xlsxwriter
        except ImportError:
            return request.make_response(
                "xlsxwriter library not available",
                headers=[('Content-Type', 'text/plain')]
            )
        
        # Get filter parameters
        filters = {
            'user': kw.get('user') or None,
            'customer': kw.get('customer') or None,
            'project': kw.get('project') or None,
            'start_date': kw.get('start_date') or None,
            'end_date': kw.get('end_date') or None,
        }
        
        # Create Excel workbook in memory
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        
        # Formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#8b5cf6',
            'font_color': 'white',
            'border': 1,
        })
        cell_format = workbook.add_format({'border': 1})
        
        # ===== Sheet 1: KPI Summary =====
        ws_kpi = workbook.add_worksheet('KPI Summary')
        ws_kpi.set_column('A:A', 25)
        ws_kpi.set_column('B:B', 15)
        
        # Get KPI data
        today = fields.Date.context_today(request.env.user)
        uid = request.env.uid
        Task = request.env['project.task']
        Project = request.env['project.project']
        
        task_domain = self._get_filter_domain(filters, model='task', env=request.env)
        project_domain = self._get_filter_domain(filters, model='project', include_dates=False, env=request.env)
        
        all_tasks = Task.search(task_domain) if task_domain else Task.search([])
        all_projects = Project.search(project_domain) if project_domain else Project.search([])
        
        my_tasks = all_tasks.filtered(lambda t: uid in t.user_ids.ids)
        active_tasks = all_tasks.filtered(lambda t: not t.stage_id.fold)
        overdue_tasks = all_tasks.filtered(
            lambda t: t.date_deadline and self._as_date(t.date_deadline, request.env.user) < today and not t.stage_id.fold
        )
        today_tasks = all_tasks.filtered(
            lambda t: t.date_deadline and self._as_date(t.date_deadline, request.env.user) == today and not t.stage_id.fold
        )
        
        kpi_data = [
            ('KPI Metric', 'Value'),
            ('My Tasks', len(my_tasks)),
            ('Total Projects', len(all_projects)),
            ('Active Tasks', len(active_tasks)),
            ('Overdue Tasks', len(overdue_tasks)),
            ("Today's Tasks", len(today_tasks)),
            ('Export Date', str(today)),
        ]
        
        for row, (label, value) in enumerate(kpi_data):
            if row == 0:
                ws_kpi.write(row, 0, label, header_format)
                ws_kpi.write(row, 1, value, header_format)
            else:
                ws_kpi.write(row, 0, label, cell_format)
                ws_kpi.write(row, 1, value, cell_format)
        
        # ===== Sheet 2: Tasks List =====
        ws_tasks = workbook.add_worksheet('Tasks')
        ws_tasks.set_column('A:A', 40)
        ws_tasks.set_column('B:B', 30)
        ws_tasks.set_column('C:C', 15)
        ws_tasks.set_column('D:D', 15)
        ws_tasks.set_column('E:E', 20)
        
        task_headers = ['Task Name', 'Project', 'Deadline', 'Priority', 'Stage']
        for col, header in enumerate(task_headers):
            ws_tasks.write(0, col, header, header_format)
        
        priority_map = {'0': 'Low', '1': 'Medium', '2': 'High', '3': 'Urgent'}
        
        for row, task in enumerate(all_tasks[:500], start=1):  # Limit to 500 rows
            ws_tasks.write(row, 0, task.name, cell_format)
            ws_tasks.write(row, 1, task.project_id.name if task.project_id else '', cell_format)
            ws_tasks.write(row, 2, str(task.date_deadline) if task.date_deadline else '', cell_format)
            ws_tasks.write(row, 3, priority_map.get(task.priority, 'Low'), cell_format)
            ws_tasks.write(row, 4, task.stage_id.name if task.stage_id else '', cell_format)
        
        # ===== Sheet 3: Activities =====
        ws_activities = workbook.add_worksheet('Activities')
        ws_activities.set_column('A:A', 40)
        ws_activities.set_column('B:B', 20)
        ws_activities.set_column('C:C', 30)
        ws_activities.set_column('D:D', 15)
        
        Activity = request.env['mail.activity']
        activities = Activity.search([
            ('user_id', '=', uid),
            ('res_model', 'in', ['project.task', 'project.project']),
        ], limit=500)
        
        activity_headers = ['Record', 'Activity Type', 'Summary', 'Due Date']
        for col, header in enumerate(activity_headers):
            ws_activities.write(0, col, header, header_format)
        
        for row, act in enumerate(activities, start=1):
            ws_activities.write(row, 0, act.res_name or '', cell_format)
            ws_activities.write(row, 1, act.activity_type_id.name if act.activity_type_id else '', cell_format)
            ws_activities.write(row, 2, act.summary or '', cell_format)
            ws_activities.write(row, 3, str(act.date_deadline) if act.date_deadline else '', cell_format)
        
        workbook.close()
        output.seek(0)
        
        # Generate filename with date
        filename = f"PTT_Dashboard_Export_{today}.xlsx"
        
        return request.make_response(
            output.read(),
            headers=[
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', f'attachment; filename="{filename}"'),
            ]
        )
