from odoo import models, fields, api


class PttDashboardConfig(models.Model):
    """Dashboard Configuration - Singleton model for main dashboard settings."""
    _name = "ptt.dashboard.config"
    _description = "PTT Dashboard Configuration"
    _rec_name = "display_name"

    # Singleton pattern - only one record
    def _get_singleton(self):
        config = self.search([], limit=1)
        if not config:
            config = self.create({})
        return config

    @api.model
    def get_config(self):
        """Get or create the singleton configuration record."""
        return self._get_singleton()

    display_name = fields.Char(
        compute="_compute_display_name",
        string="Dashboard Configuration"
    )

    # Default date ranges
    default_date_range = fields.Selection([
        ('today', 'Today'),
        ('this_week', 'This Week'),
        ('this_month', 'This Month'),
        ('this_quarter', 'This Quarter'),
        ('this_year', 'This Year'),
    ], string="Default Date Range", default='this_month')

    # User filter settings
    show_all_users = fields.Boolean(
        string="Show All Users",
        default=True,
        help="Show all active users in 'All Users' sections. If False, use user_filter_domain."
    )
    
    user_filter_domain = fields.Char(
        string="User Filter Domain",
        help="Domain to filter users (e.g., [('groups_id', 'in', [ref('base.group_salesman')])])"
    )
    
    min_events_to_show = fields.Integer(
        string="Minimum Events to Show",
        default=0,
        help="Minimum number of events/revenue for a user to appear in 'All Users' sections"
    )

    # Company-wide settings
    enable_export = fields.Boolean(
        string="Enable Export",
        default=True,
        help="Allow users to export dashboard data"
    )

    @api.depends()
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = "Dashboard Configuration"

