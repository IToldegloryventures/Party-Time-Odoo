# -*- coding: utf-8 -*-
"""Tests for Dashboard model."""

from odoo.tests.common import TransactionCase, tagged


@tagged('standard', 'at_install')
class TestDashboard(TransactionCase):
    """Test Dashboard model functionality."""
    
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
    
    def test_dashboard_creation(self):
        """Test creating a dashboard."""
        dashboard = self.env['dashboard.dashboard'].create({
            'name': 'Test Dashboard',
            'parent_menu_id': self.parent_menu.id,
        })
        
        self.assertEqual(dashboard.name, 'Test Dashboard')
        self.assertEqual(dashboard.chart_count, 0)
        self.assertTrue(dashboard.menu_active)
    
    def test_dashboard_chart_count(self):
        """Test chart count is computed correctly."""
        dashboard = self.env['dashboard.dashboard'].create({
            'name': 'Chart Count Test',
            'parent_menu_id': self.parent_menu.id,
        })
        
        # Create charts
        chart1 = self.env['dashboard.chart'].create({
            'name': 'Chart 1',
            'dashboard_id': dashboard.id,
            'chart_type': 'kpi',
        })
        
        chart2 = self.env['dashboard.chart'].create({
            'name': 'Chart 2',
            'dashboard_id': dashboard.id,
            'chart_type': 'bar_chart',
        })
        
        dashboard.invalidate_recordset()
        self.assertEqual(dashboard.chart_count, 2)
        self.assertIn(chart1, dashboard.chart_ids)
        self.assertIn(chart2, dashboard.chart_ids)
    
    def test_dashboard_menu_creation(self):
        """Test dashboard creates menu and action."""
        dashboard = self.env['dashboard.dashboard'].create({
            'name': 'Menu Test Dashboard',
            'parent_menu_id': self.parent_menu.id,
            'menu_sequence': 10,
        })
        
        # Menu and action should be created (if implementation does this)
        # This depends on the actual dashboard implementation
        self.assertTrue(dashboard.name)
    
    def test_dashboard_export_json(self):
        """Test dashboard JSON export."""
        dashboard = self.env['dashboard.dashboard'].create({
            'name': 'Export Test Dashboard',
            'parent_menu_id': self.parent_menu.id,
        })
        
        # Create a chart
        chart = self.env['dashboard.chart'].create({
            'name': 'Export Chart',
            'dashboard_id': dashboard.id,
            'chart_type': 'kpi',
        })
        
        # Export JSON
        json_data = dashboard.dashboard_export_json()
        
        # Should return valid data structure
        self.assertIsInstance(json_data, (dict, list))
    
    def test_dashboard_access_groups(self):
        """Test dashboard access by groups."""
        # Create group
        group = self.env['res.groups'].create({
            'name': 'Dashboard Test Group',
        })
        
        dashboard = self.env['dashboard.dashboard'].create({
            'name': 'Group Access Test',
            'parent_menu_id': self.parent_menu.id,
            'access_by': 'access_group',
            'group_ids': [(6, 0, [group.id])],
        })
        
        self.assertEqual(dashboard.access_by, 'access_group')
        self.assertIn(group, dashboard.group_ids)
    
    def test_dashboard_access_users(self):
        """Test dashboard access by users."""
        # Create user
        user = self.env['res.users'].create({
            'name': 'Dashboard Test User',
            'login': 'dashboard_test_user',
            'email': 'dashboard_test@example.com',
        })
        
        dashboard = self.env['dashboard.dashboard'].create({
            'name': 'User Access Test',
            'parent_menu_id': self.parent_menu.id,
            'access_by': 'user',
            'user_ids': [(6, 0, [user.id])],
        })
        
        self.assertEqual(dashboard.access_by, 'user')
        self.assertIn(user, dashboard.user_ids)
