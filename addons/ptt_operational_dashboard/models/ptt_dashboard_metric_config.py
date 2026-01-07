from odoo import models, fields, api


class PttDashboardMetricConfig(models.Model):
    """Dashboard Metric Configuration - Controls visibility, order, size, thresholds for each metric."""
    _name = "ptt.dashboard.metric.config"
    _description = "PTT Dashboard Metric Configuration"
    _order = "sequence, id"
    _rec_name = "metric_name"

    # Metric identification
    metric_name = fields.Char(
        string="Metric Name",
        required=True,
        index=True,
        help="Unique identifier for the metric (e.g., 'total_booked', 'capture_rate')"
    )
    
    metric_label = fields.Char(
        string="Display Label",
        required=True,
        help="Human-readable label for the metric"
    )

    # Visibility and display
    visible = fields.Boolean(
        string="Visible",
        default=True,
        help="Whether this metric is visible on the dashboard"
    )
    
    sequence = fields.Integer(
        string="Display Order",
        default=10,
        help="Order in which metrics appear (lower numbers first)"
    )
    
    kpi_size = fields.Selection([
        ('large', 'Large'),
        ('compact', 'Compact'),
    ], string="KPI Size", default='compact',
        help="Size of the KPI card"
    )

    # Tab assignment
    tab_assignment = fields.Selection([
        ('sales', 'Sales Dashboard'),
        ('operations', 'Operations Dashboard'),
        ('communication', 'Communication Dashboard'),
        ('home', 'Home Tab'),
    ], string="Tab", required=True, default='sales',
        help="Which dashboard tab this metric belongs to"
    )

    # Color thresholds
    threshold_green_min = fields.Float(
        string="Green Threshold (Min)",
        default=0.0,
        help="Minimum value for green color coding"
    )
    
    threshold_yellow_min = fields.Float(
        string="Yellow Threshold (Min)",
        default=0.0,
        help="Minimum value for yellow color coding"
    )
    
    threshold_red_max = fields.Float(
        string="Red Threshold (Max)",
        default=0.0,
        help="Maximum value for red color coding"
    )

    # Target values
    target_value = fields.Float(
        string="Target Value",
        help="Target value for this metric (used for comparisons)"
    )

    # Additional settings
    show_trend = fields.Boolean(
        string="Show Trend Indicator",
        default=False,
        help="Show up/down trend arrows"
    )
    
    format_type = fields.Selection([
        ('currency', 'Currency'),
        ('percentage', 'Percentage'),
        ('number', 'Number'),
        ('days', 'Days'),
        ('hours', 'Hours'),
    ], string="Format Type", default='number',
        help="How to format the metric value"
    )

    @api.model
    def get_visible_metrics(self, tab=None):
        """Get all visible metrics, optionally filtered by tab.
        
        Args:
            tab: Tab name to filter by (optional)
        
        Returns:
            Recordset of visible metric configs, ordered by sequence
        """
        domain = [("visible", "=", True)]
        if tab:
            domain.append(("tab_assignment", "=", tab))
        return self.search(domain, order="sequence, id")

