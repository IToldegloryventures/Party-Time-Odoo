from odoo import models, fields


class TeamDashboardHub(models.Model):
    """Team Dashboard Hub - unified view of tasks, calendars, and dashboards"""
    _name = 'ppt.team.dashboard.hub'
    _description = 'Team Dashboard Hub'

    user_id = fields.Many2one('res.users', 'User', required=True, default=lambda self: self.env.user)
    dashboard_ids = fields.Many2many('ppt.team.dashboard.config', 'hub_dashboard_rel', 'hub_id', 'dashboard_id', 'Active Dashboards')
    
    # View Preferences
    show_tasks = fields.Boolean('Show Tasks', default=True)
    show_calendars = fields.Boolean('Show Calendars', default=True)
    show_dashboards = fields.Boolean('Show Dashboards', default=True)
    show_notifications = fields.Boolean('Show Notifications', default=True)
    
    # Layout
    layout_mode = fields.Selection([
        ('grid', '4-Column Grid'),
        ('list', 'List View'),
        ('kanban', 'Kanban Board'),
    ], 'Layout', default='grid')
    
    theme = fields.Selection([
        ('light', 'Light'),
        ('dark', 'Dark'),
        ('auto', 'Auto (System)'),
    ], 'Theme', default='light')
    
    # Sidebar
    sidebar_collapsed = fields.Boolean('Sidebar Collapsed', default=False)
    sidebar_position = fields.Selection([
        ('left', 'Left'),
        ('right', 'Right'),
    ], 'Sidebar Position', default='left')
