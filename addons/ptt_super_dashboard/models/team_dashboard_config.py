from odoo import models, fields


class TeamDashboardConfig(models.Model):
    """Store team dashboard configurations"""
    _name = 'ptt.team.dashboard.config'
    _description = 'Team Dashboard Configuration'
    _order = 'sequence, name'

    name = fields.Char('Dashboard Name', required=True)
    description = fields.Text('Description')
    user_id = fields.Many2one('res.users', 'Owner', default=lambda self: self.env.user)
    is_public = fields.Boolean('Public', default=False)
    is_active = fields.Boolean('Active', default=True)
    
    # Layout & Refresh
    auto_refresh_interval = fields.Integer('Auto Refresh (seconds)', default=300)
    layout_config = fields.Json('Layout Config', default={})
    theme_config = fields.Json('Theme Config', default={})
    
    # Widgets & Layout
    widget_ids = fields.One2many('ptt.team.dashboard.widget', 'dashboard_id', 'Widgets')
    sequence = fields.Integer('Sequence', default=10)
    
    # Access Control
    allowed_user_ids = fields.Many2many('res.users', 'dashboard_user_rel', 'dashboard_id', 'user_id', 'Allowed Users')
    allowed_group_ids = fields.Many2many('res.groups', 'dashboard_group_rel', 'dashboard_id', 'group_id', 'Allowed Groups')
    
    # Timestamps
    create_date = fields.Datetime('Created', readonly=True)
    write_date = fields.Datetime('Modified', readonly=True)


class TeamDashboardWidget(models.Model):
    """Individual widget in a dashboard"""
    _name = 'ptt.team.dashboard.widget'
    _description = 'Team Dashboard Widget'
    _order = 'sequence, name'

    name = fields.Char('Widget Name', required=True)
    dashboard_id = fields.Many2one('ptt.team.dashboard.config', 'Dashboard', required=True, ondelete='cascade')
    
    # Widget Type
    widget_type = fields.Selection([
        ('kpi', 'KPI Card'),
        ('bar_chart', 'Bar Chart'),
        ('line_chart', 'Line Chart'),
        ('pie_chart', 'Pie Chart'),
        ('gauge', 'Gauge'),
        ('table', 'Data Table'),
        ('metric', 'Metric'),
        ('text', 'Text'),
    ], 'Widget Type', default='kpi', required=True)
    
    # Position & Size (grid-based: 12 columns)
    position_x = fields.Integer('Position X', default=0, min=0)
    position_y = fields.Integer('Position Y', default=0, min=0)
    width = fields.Integer('Width (columns)', default=3, min=1, max=12)
    height = fields.Integer('Height (rows)', default=2, min=1)
    position_config = fields.Json('Position Config', default={})
    
    # Data Source
    data_source_type = fields.Selection([
        ('model', 'Odoo Model'),
        ('sql', 'SQL Query'),
        ('api', 'External API'),
    ], 'Data Source Type', default='model')
    data_source_config = fields.Json('Data Source Config', default={})
    
    # Widget Configuration
    widget_config = fields.Json('Widget Config', default={})
    
    # Status
    is_active = fields.Boolean('Active', default=True)
    sequence = fields.Integer('Sequence', default=10)
