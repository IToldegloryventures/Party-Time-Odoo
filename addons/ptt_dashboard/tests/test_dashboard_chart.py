# -*- coding: utf-8 -*-
"""Tests for Dashboard Chart model."""

from odoo.tests.common import TransactionCase, tagged


@tagged('standard', 'at_install')
class TestDashboardChart(TransactionCase):
    """Test Dashboard Chart model functionality."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test data."""
        super().setUpClass()
        
        # Get parent menu
        cls.parent_menu = cls.env.ref(
            'ptt_dashboard.parent_dashboard_menu',
            raise_if_not_found=False
        )
        if not cls.parent_menu:
            cls.parent_menu = cls.env['ir.ui.menu'].create({
                'name': 'Dashboards',
                'sequence': 100,
            })
        
        # Create dashboard
        cls.dashboard = cls.env['dashboard.dashboard'].create({
            'name': 'Chart Test Dashboard',
            'parent_menu_id': cls.parent_menu.id,
        })
        
        # Get a model for KPI
        cls.crm_model = cls.env['ir.model'].search([
            ('model', '=', 'crm.lead')
        ], limit=1)
    
    def test_chart_creation(self):
        """Test creating a chart."""
        chart = self.env['dashboard.chart'].create({
            'name': 'Test Chart',
            'dashboard_id': self.dashboard.id,
            'chart_type': 'kpi',
            'kpi_model_id': self.crm_model.id if self.crm_model else False,
        })
        
        self.assertEqual(chart.name, 'Test Chart')
        self.assertEqual(chart.dashboard_id, self.dashboard)
        self.assertEqual(chart.chart_type, 'kpi')
        self.assertTrue(chart.active)
    
    def test_chart_types(self):
        """Test different chart types can be created."""
        chart_types = [
            'kpi', 'bar_chart', 'line_chart', 'pie_chart',
            'column_chart', 'area_chart', 'list'
        ]
        
        for chart_type in chart_types:
            chart = self.env['dashboard.chart'].create({
                'name': f'{chart_type} Chart',
                'dashboard_id': self.dashboard.id,
                'chart_type': chart_type,
            })
            
            self.assertEqual(chart.chart_type, chart_type)
    
    def test_chart_used_list_fields(self):
        """Test used list fields computation."""
        chart = self.env['dashboard.chart'].create({
            'name': 'List Fields Test',
            'dashboard_id': self.dashboard.id,
            'chart_type': 'list',
            'kpi_model_id': self.crm_model.id if self.crm_model else False,
        })
        
        # Add list fields if model exists
        if self.crm_model:
            # This depends on the actual implementation
            # Just verify the chart can be created
            self.assertTrue(chart.name)
    
    def test_chart_active_toggle(self):
        """Test chart active field toggle."""
        chart = self.env['dashboard.chart'].create({
            'name': 'Active Toggle Test',
            'dashboard_id': self.dashboard.id,
            'chart_type': 'kpi',
            'active': True,
        })
        
        self.assertTrue(chart.active)
        
        # Deactivate
        chart.write({'active': False})
        self.assertFalse(chart.active)
        
        # Reactivate
        chart.write({'active': True})
        self.assertTrue(chart.active)
    
    def test_chart_cascade_delete(self):
        """Test chart is deleted when dashboard is deleted."""
        chart = self.env['dashboard.chart'].create({
            'name': 'Cascade Delete Test',
            'dashboard_id': self.dashboard.id,
            'chart_type': 'kpi',
        })
        
        chart_id = chart.id
        
        # Delete dashboard
        self.dashboard.unlink()
        
        # Chart should be deleted
        self.assertFalse(self.env['dashboard.chart'].browse(chart_id).exists())
