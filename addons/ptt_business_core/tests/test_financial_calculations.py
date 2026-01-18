# -*- coding: utf-8 -*-
"""Tests for financial calculations."""

from odoo.tests.common import TransactionCase


class TestFinancialCalculations(TransactionCase):
    """Test financial calculation accuracy across models."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test data."""
        super().setUpClass()
        
        cls.partner = cls.env['res.partner'].create({
            'name': 'Financial Test Client',
            'email': 'finance@example.com',
        })
        
        cls.vendor = cls.env['res.partner'].create({
            'name': 'Test Vendor',
            'email': 'vendor@example.com',
            'ptt_is_vendor': True,
        })
        
    def test_crm_margin_calculation_basic(self):
        """Test basic margin calculation on CRM lead."""
        lead = self.env['crm.lead'].create({
            'name': 'Margin Test',
            'partner_id': self.partner.id,
            'ptt_estimated_client_total': 10000.00,
        })
        
        # Add vendor costs
        self.env['ptt.crm.vendor.estimate'].create({
            'crm_lead_id': lead.id,
            'service_type': 'dj',
            'estimated_cost': 2000.00,
        })
        
        self.env['ptt.crm.vendor.estimate'].create({
            'crm_lead_id': lead.id,
            'service_type': 'photovideo',
            'estimated_cost': 1500.00,
        })
        
        self.env['ptt.crm.vendor.estimate'].create({
            'crm_lead_id': lead.id,
            'service_type': 'lighting',
            'estimated_cost': 500.00,
        })
        
        lead.invalidate_recordset()
        
        # Total costs: 2000 + 1500 + 500 = 4000
        self.assertEqual(lead.ptt_estimated_vendor_total, 4000.00)
        # Margin: 10000 - 4000 = 6000
        self.assertEqual(lead.ptt_estimated_margin, 6000.00)
        # Margin %: 6000/10000 * 100 = 60%
        self.assertEqual(lead.ptt_margin_percent, 60.0)
        
    def test_crm_margin_zero_client_total(self):
        """Test margin calculation when client total is zero."""
        lead = self.env['crm.lead'].create({
            'name': 'Zero Total Test',
            'partner_id': self.partner.id,
            'ptt_estimated_client_total': 0.00,
        })
        
        self.env['ptt.crm.vendor.estimate'].create({
            'crm_lead_id': lead.id,
            'service_type': 'dj',
            'estimated_cost': 500.00,
        })
        
        lead.invalidate_recordset()
        
        self.assertEqual(lead.ptt_estimated_vendor_total, 500.00)
        self.assertEqual(lead.ptt_estimated_margin, -500.00)
        self.assertEqual(lead.ptt_margin_percent, 0.0)  # Avoid division by zero
        
    def test_project_margin_calculation(self):
        """Test margin calculation on project."""
        project = self.env['project.project'].create({
            'name': 'Project Margin Test',
            'partner_id': self.partner.id,
            'ptt_client_total': 15000.00,
        })
        
        # Add vendor assignments with actual costs
        self.env['ptt.project.vendor.assignment'].create({
            'project_id': project.id,
            'service_type': 'dj',
            'vendor_id': self.vendor.id,
            'estimated_cost': 2000.00,
            'actual_cost': 1800.00,
        })
        
        self.env['ptt.project.vendor.assignment'].create({
            'project_id': project.id,
            'service_type': 'photovideo',
            'vendor_id': self.vendor.id,
            'estimated_cost': 1500.00,
            'actual_cost': 1700.00,
        })
        
        project.invalidate_recordset()
        
        # Estimated: 2000 + 1500 = 3500
        self.assertEqual(project.ptt_total_estimated_cost, 3500.00)
        # Actual: 1800 + 1700 = 3500
        self.assertEqual(project.ptt_total_actual_cost, 3500.00)
        # Variance: 3500 - 3500 = 0 (exactly on budget!)
        self.assertEqual(project.ptt_cost_variance, 0.00)
        # Margin: 15000 - 3500 = 11500
        self.assertEqual(project.ptt_actual_margin, 11500.00)
        # Margin %: 11500/15000 * 100 = 76.67%
        self.assertAlmostEqual(project.ptt_margin_percent, 76.67, places=1)
        
    def test_cost_variance_over_budget(self):
        """Test cost variance when over budget."""
        project = self.env['project.project'].create({
            'name': 'Over Budget Test',
            'partner_id': self.partner.id,
            'ptt_client_total': 5000.00,
        })
        
        self.env['ptt.project.vendor.assignment'].create({
            'project_id': project.id,
            'service_type': 'dj',
            'vendor_id': self.vendor.id,
            'estimated_cost': 1000.00,
            'actual_cost': 1500.00,  # $500 over
        })
        
        project.invalidate_recordset()
        
        # Positive variance = over budget
        self.assertEqual(project.ptt_cost_variance, 500.00)
        
    def test_cost_variance_under_budget(self):
        """Test cost variance when under budget."""
        project = self.env['project.project'].create({
            'name': 'Under Budget Test',
            'partner_id': self.partner.id,
            'ptt_client_total': 5000.00,
        })
        
        self.env['ptt.project.vendor.assignment'].create({
            'project_id': project.id,
            'service_type': 'dj',
            'vendor_id': self.vendor.id,
            'estimated_cost': 1000.00,
            'actual_cost': 800.00,  # $200 under
        })
        
        project.invalidate_recordset()
        
        # Negative variance = under budget (good!)
        self.assertEqual(project.ptt_cost_variance, -200.00)
        
    def test_multiple_vendors_aggregation(self):
        """Test financial aggregation with multiple vendors."""
        project = self.env['project.project'].create({
            'name': 'Multi Vendor Test',
            'partner_id': self.partner.id,
            'ptt_client_total': 20000.00,
        })
        
        # Create 5 vendor assignments
        services = ['dj', 'photovideo', 'lighting', 'decor', 'catering']
        for i, service in enumerate(services, 1):
            self.env['ptt.project.vendor.assignment'].create({
                'project_id': project.id,
                'service_type': service,
                'vendor_id': self.vendor.id,
                'estimated_cost': 1000.00 * i,
                'actual_cost': 1100.00 * i,
            })
        
        project.invalidate_recordset()
        
        # Estimated: 1000 + 2000 + 3000 + 4000 + 5000 = 15000
        self.assertEqual(project.ptt_total_estimated_cost, 15000.00)
        # Actual: 1100 + 2200 + 3300 + 4400 + 5500 = 16500
        self.assertEqual(project.ptt_total_actual_cost, 16500.00)
        # Vendor count
        self.assertEqual(project.ptt_vendor_count, 5)
