# Part of Party Time Texas. See LICENSE file for full copyright and licensing details.
"""
Dashboard Filter Presets Model.

Allows users to save and recall filter combinations for the PTT Project Dashboard.
Each preset stores the filter state (manager, customer, project, date range) as JSON.
"""

import json
from odoo import models, fields, api


class PTTDashboardFilterPreset(models.Model):
    """Saved filter presets for the PTT Project Dashboard."""
    
    _name = 'ptt.dashboard.filter.preset'
    _description = 'Dashboard Filter Preset'
    _order = 'name'
    
    name = fields.Char(
        string='Preset Name',
        required=True,
        help="Name to identify this filter combination"
    )
    
    user_id = fields.Many2one(
        'res.users',
        string='User',
        required=True,
        default=lambda self: self.env.user,
        ondelete='cascade',
        help="User who created this preset"
    )
    
    filters_json = fields.Text(
        string='Filters (JSON)',
        required=True,
        default='{}',
        help="JSON-encoded filter parameters"
    )
    
    # Computed fields for display
    manager_id = fields.Many2one(
        'res.users',
        string='Manager Filter',
        compute='_compute_filter_display',
        store=False,
    )
    
    customer_id = fields.Many2one(
        'res.partner',
        string='Customer Filter',
        compute='_compute_filter_display',
        store=False,
    )
    
    project_id = fields.Many2one(
        'project.project',
        string='Project Filter',
        compute='_compute_filter_display',
        store=False,
    )
    
    date_range = fields.Char(
        string='Date Range',
        compute='_compute_filter_display',
        store=False,
    )
    
    @api.depends('filters_json')
    def _compute_filter_display(self):
        """Parse JSON and compute display fields."""
        for record in self:
            try:
                filters = json.loads(record.filters_json or '{}')
            except json.JSONDecodeError:
                filters = {}
            
            # Manager
            manager_id = filters.get('manager')
            if manager_id and str(manager_id).isdigit():
                record.manager_id = int(manager_id)
            else:
                record.manager_id = False
            
            # Customer
            customer_id = filters.get('customer')
            if customer_id and str(customer_id).isdigit():
                record.customer_id = int(customer_id)
            else:
                record.customer_id = False
            
            # Project
            project_id = filters.get('project')
            if project_id and str(project_id).isdigit():
                record.project_id = int(project_id)
            else:
                record.project_id = False
            
            # Date range
            start = filters.get('start_date')
            end = filters.get('end_date')
            if start and end:
                record.date_range = f"{start} to {end}"
            elif start:
                record.date_range = f"From {start}"
            elif end:
                record.date_range = f"Until {end}"
            else:
                record.date_range = "All time"
    
    def get_filters(self):
        """Return parsed filters dict."""
        self.ensure_one()
        try:
            return json.loads(self.filters_json or '{}')
        except json.JSONDecodeError:
            return {}
    
    def set_filters(self, filters_dict):
        """Set filters from dict."""
        self.ensure_one()
        self.filters_json = json.dumps(filters_dict)
    
    @api.model
    def get_user_presets(self):
        """Get all presets for current user."""
        return self.search([('user_id', '=', self.env.user.id)])
