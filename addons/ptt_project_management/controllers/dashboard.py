# Part of Party Time Texas. See LICENSE file for full copyright and licensing details.
"""
HTTP Controllers for PTT Project Dashboard.

Based on: Cybrosys project_dashboard_odoo/controllers/project_dashboard_odoo.py

Provides JSON-RPC endpoints for the Project Dashboard inside the Projects app.
"""

import random
from odoo import http, fields
from odoo.http import request


class PTTDashboardController(http.Controller):
    """HTTP Controller for Project Dashboard data."""

    def _get_random_color(self):
        """Generate a random hex color for charts."""
        return "#{:06x}".format(random.randint(0, 0xFFFFFF))

    @http.route('/ptt/dashboard/tiles', auth='user', type='json')
    def get_tiles_data(self):
        """Get main tile/KPI data for dashboard.

        Returns tile counts like: My Tasks, Total Projects, Active Tasks,
        My Overdue Tasks, Overdue Tasks, Today Tasks
        """
        today = fields.Date.today()
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
        active_tasks = all_tasks.filtered(lambda t: t.state not in ['1_done', '1_canceled'])

        # My tasks
        my_tasks = Task.search([('user_ids', 'in', [uid])])

        # My overdue tasks
        my_overdue = my_tasks.filtered(
            lambda t: t.date_deadline and t.date_deadline < today
            and t.state not in ['1_done', '1_canceled']
        )

        # All overdue tasks (visible to user)
        all_overdue = all_tasks.filtered(
            lambda t: t.date_deadline and t.date_deadline < today
            and t.state not in ['1_done', '1_canceled']
        )

        # Today's tasks
        today_tasks = all_tasks.filtered(
            lambda t: t.date_deadline and t.date_deadline == today
            and t.state not in ['1_done', '1_canceled']
        )

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
            'user_name': request.env.user.name,
        }

    @http.route('/ptt/dashboard/tasks', auth='user', type='json')
    def get_all_tasks(self, page=1, limit=5):
        """Get paginated task list for the All Tasks table.

        Returns tasks with: name, project, deadline, priority, stage, id
        """
        today = fields.Date.today()
        uid = request.env.uid
        Task = request.env['project.task']

        is_manager = request.env.user.has_group('project.group_project_manager')

        # Get tasks with deadlines, prioritize overdue
        if is_manager:
            domain = [('date_deadline', '!=', False)]
        else:
            domain = [('user_ids', 'in', [uid]), ('date_deadline', '!=', False)]

        # Exclude done/canceled
        domain.append(('state', 'not in', ['1_done', '1_canceled']))

        total_count = Task.search_count(domain)
        offset = (page - 1) * limit

        tasks = Task.search(domain, order='date_deadline asc', limit=limit, offset=offset)

        task_list = []
        for task in tasks:
            # Calculate days ago/until
            if task.date_deadline:
                delta = (today - task.date_deadline).days
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

    @http.route('/ptt/dashboard/task-deadline-chart', auth='user', type='json')
    def get_task_deadline_chart(self):
        """Get data for Task Deadline pie chart (Overdue/Today/Upcoming)."""
        today = fields.Date.today()
        uid = request.env.uid
        Task = request.env['project.task']

        is_manager = request.env.user.has_group('project.group_project_manager')

        if is_manager:
            base_domain = [('state', 'not in', ['1_done', '1_canceled'])]
        else:
            base_domain = [('user_ids', 'in', [uid]), ('state', 'not in', ['1_done', '1_canceled'])]

        overdue = Task.search_count(base_domain + [('date_deadline', '<', today)])
        today_count = Task.search_count(base_domain + [('date_deadline', '=', today)])
        upcoming = Task.search_count(base_domain + [('date_deadline', '>', today)])

        return {
            'labels': ['Overdue', 'Today', 'Upcoming'],
            'data': [overdue, today_count, upcoming],
            'colors': ['#95a5a6', '#f1c40f', '#9b59b6'],  # Gray, Yellow, Purple
        }

    @http.route('/ptt/dashboard/task-stages-chart', auth='user', type='json')
    def get_task_stages_chart(self):
        """Get data for Task By Stages doughnut chart."""
        uid = request.env.uid
        Task = request.env['project.task']
        Stage = request.env['project.task.type']

        is_manager = request.env.user.has_group('project.group_project_manager')

        if is_manager:
            base_domain = []
        else:
            base_domain = [('user_ids', 'in', [uid])]

        stages = Stage.search([])

        labels = []
        data = []
        colors = ['#e74c3c', '#2ecc71', '#3498db', '#9b59b6', '#f39c12', '#1abc9c']

        for idx, stage in enumerate(stages):
            count = Task.search_count(base_domain + [('stage_id', '=', stage.id)])
            if count > 0:
                labels.append(stage.name)
                data.append(count)

        return {
            'labels': labels,
            'data': data,
            'colors': colors[:len(labels)],
        }

    @http.route('/ptt/dashboard/task-project-chart', auth='user', type='json')
    def get_task_project_chart(self):
        """Get data for Task By Project bar chart."""
        uid = request.env.uid
        Project = request.env['project.project']
        Task = request.env['project.task']

        is_manager = request.env.user.has_group('project.group_project_manager')

        if is_manager:
            projects = Project.search([], limit=10, order='create_date desc')
        else:
            projects = Project.search([
                '|',
                ('user_id', '=', uid),
                ('message_partner_ids', 'in', [request.env.user.partner_id.id]),
            ], limit=10, order='create_date desc')

        labels = []
        data = []
        colors = ['#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6', '#1abc9c']

        for project in projects:
            task_count = Task.search_count([('project_id', '=', project.id)])
            if task_count > 0:
                labels.append(project.name[:15] + '...' if len(project.name) > 15 else project.name)
                data.append(task_count)

        return {
            'labels': labels,
            'data': data,
            'colors': colors[:len(labels)],
        }

    @http.route('/ptt/dashboard/priority-chart', auth='user', type='json')
    def get_priority_chart(self):
        """Get data for Priority Wise bar chart."""
        uid = request.env.uid
        Task = request.env['project.task']

        is_manager = request.env.user.has_group('project.group_project_manager')

        if is_manager:
            base_domain = [('state', 'not in', ['1_done', '1_canceled'])]
        else:
            base_domain = [('user_ids', 'in', [uid]), ('state', 'not in', ['1_done', '1_canceled'])]

        # Odoo uses priority 0 = Low, 1 = High (starred)
        low_priority = Task.search_count(base_domain + [('priority', '=', '0')])
        high_priority = Task.search_count(base_domain + [('priority', '=', '1')])

        return {
            'labels': ['Low', 'High'],
            'data': [low_priority, high_priority],
            'colors': ['#5dade2', '#ec7063'],  # Light blue, Light red
        }

    @http.route('/ptt/dashboard/activities', auth='user', type='json')
    def get_activities(self, page=1, limit=5):
        """Get paginated activities list."""
        uid = request.env.uid
        Activity = request.env['mail.activity']

        domain = [
            ('user_id', '=', uid),
            ('res_model', 'in', ['project.task', 'project.project']),
        ]

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

    @http.route('/ptt/dashboard/filter', auth='user', type='json')
    def get_filter_options(self):
        """Get filter dropdown options (managers, customers, projects)."""
        User = request.env['res.users']
        Partner = request.env['res.partner']
        Project = request.env['project.project']

        # Get project managers
        manager_group = request.env.ref('project.group_project_manager', raise_if_not_found=False)
        if manager_group:
            managers = User.search([('groups_id', 'in', [manager_group.id])])
        else:
            managers = User.search([])
        manager_list = [{'id': m.id, 'name': m.name} for m in managers]

        # Get customers (partners with projects)
        projects = Project.search([])
        customer_ids = projects.mapped('partner_id').ids
        customers = Partner.browse(list(set(customer_ids)))
        customer_list = [{'id': c.id, 'name': c.name} for c in customers if c]

        # Get projects
        project_list = [{'id': p.id, 'name': p.name} for p in projects]

        return {
            'managers': manager_list,
            'customers': customer_list,
            'projects': project_list,
        }

    @http.route('/ptt/dashboard/filter-apply', auth='user', type='json')
    def apply_filter(self, **kw):
        """Apply filters and return filtered data."""
        data = kw.get('data', {})

        manager_id = data.get('manager')
        customer_id = data.get('customer')
        project_id = data.get('project')
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        today = fields.Date.today()
        uid = request.env.uid
        Task = request.env['project.task']
        Project = request.env['project.project']

        # Build project domain
        project_domain = []
        if project_id and project_id != 'null':
            project_domain.append(('id', '=', int(project_id)))
        if manager_id and manager_id != 'null':
            project_domain.append(('user_id', '=', int(manager_id)))
        if customer_id and customer_id != 'null':
            project_domain.append(('partner_id', '=', int(customer_id)))

        filtered_projects = Project.search(project_domain) if project_domain else Project.search([])

        # Build task domain
        task_domain = [('project_id', 'in', filtered_projects.ids)] if filtered_projects else []

        if start_date and start_date != 'null':
            task_domain.append(('date_deadline', '>=', start_date))
        if end_date and end_date != 'null':
            task_domain.append(('date_deadline', '<=', end_date))

        # Get filtered tasks
        all_tasks = Task.search(task_domain) if task_domain else Task.search([])
        active_tasks = all_tasks.filtered(lambda t: t.state not in ['1_done', '1_canceled'])
        my_tasks = all_tasks.filtered(lambda t: uid in t.user_ids.ids)
        my_overdue = my_tasks.filtered(
            lambda t: t.date_deadline and t.date_deadline < today
            and t.state not in ['1_done', '1_canceled']
        )
        all_overdue = all_tasks.filtered(
            lambda t: t.date_deadline and t.date_deadline < today
            and t.state not in ['1_done', '1_canceled']
        )
        today_tasks = all_tasks.filtered(
            lambda t: t.date_deadline and t.date_deadline == today
            and t.state not in ['1_done', '1_canceled']
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
