# -*- coding: utf-8 -*-
"""Tests for Project Vendor Assignment model."""

from odoo.tests.common import TransactionCase


class TestProjectVendorAssignment(TransactionCase):
    """Test vendor assignment functionality."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test data."""
        super().setUpClass()
        
        # Create a test partner (customer)
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Event Client',
            'email': 'client@example.com',
        })
        
        # Create test vendor partners
        cls.vendor_dj = cls.env['res.partner'].create({
            'name': 'DJ Pro Services',
            'email': 'dj@example.com',
            'supplier_rank': 1,
        })
        
        cls.vendor_photo = cls.env['res.partner'].create({
            'name': 'Photo Magic Studios',
            'email': 'photo@example.com',
            'supplier_rank': 1,
        })
        
        # Create a test project
        cls.project = cls.env['project.project'].create({
            'name': 'Test Event Project',
            'partner_id': cls.partner.id,
            'x_studio_event_name': 'Test Gala',
            'x_studio_event_date': '2026-06-15',
            'ptt_client_total': 10000.00,
        })
        
    def test_vendor_assignment_creation(self):
        """Test creating a vendor assignment."""
        assignment = self.env['ptt.project.vendor.assignment'].create({
            'project_id': self.project.id,
            'service_type': 'dj',
            'vendor_id': self.vendor_dj.id,
            'estimated_cost': 800.00,
            'actual_cost': 750.00,
        })
        
        self.assertEqual(assignment.vendor_name, 'DJ Pro Services')
        self.assertEqual(assignment.status, 'pending')
        
    def test_cost_variance_computed(self):
        """Test cost variance is calculated correctly."""
        assignment = self.env['ptt.project.vendor.assignment'].create({
            'project_id': self.project.id,
            'service_type': 'dj',
            'vendor_id': self.vendor_dj.id,
            'estimated_cost': 1000.00,
            'actual_cost': 850.00,
        })
        
        # Under budget should be negative variance
        self.assertEqual(assignment.cost_variance, -150.00)
        
        # Over budget
        assignment.actual_cost = 1200.00
        assignment.invalidate_recordset()
        self.assertEqual(assignment.cost_variance, 200.00)
        
    def test_project_vendor_stats_computed(self):
        """Test project vendor statistics are computed."""
        # Add two vendor assignments
        self.env['ptt.project.vendor.assignment'].create({
            'project_id': self.project.id,
            'service_type': 'dj',
            'vendor_id': self.vendor_dj.id,
            'estimated_cost': 1000.00,
            'actual_cost': 950.00,
        })
        
        self.env['ptt.project.vendor.assignment'].create({
            'project_id': self.project.id,
            'service_type': 'photography',
            'vendor_id': self.vendor_photo.id,
            'estimated_cost': 1500.00,
            'actual_cost': 1600.00,
        })
        
        # Recompute
        self.project.invalidate_recordset()
        
        self.assertEqual(self.project.ptt_vendor_count, 2)
        self.assertEqual(self.project.ptt_total_estimated_cost, 2500.00)
        self.assertEqual(self.project.ptt_total_actual_cost, 2550.00)
        self.assertEqual(self.project.ptt_cost_variance, 50.00)
        
        # Margin calculation
        self.assertEqual(self.project.ptt_actual_margin, 7450.00)  # 10000 - 2550
        
    def test_vendor_name_denormalized(self):
        """Test vendor name is stored for search efficiency."""
        assignment = self.env['ptt.project.vendor.assignment'].create({
            'project_id': self.project.id,
            'service_type': 'dj',
            'vendor_id': self.vendor_dj.id,
            'estimated_cost': 800.00,
        })
        
        self.assertEqual(assignment.vendor_name, 'DJ Pro Services')
        
        # Change vendor
        assignment.vendor_id = self.vendor_photo
        assignment.invalidate_recordset()
        
        self.assertEqual(assignment.vendor_name, 'Photo Magic Studios')
        
    def test_vendor_contact_onchange(self):
        """Test vendor contact is populated on vendor selection."""
        assignment = self.env['ptt.project.vendor.assignment'].create({
            'project_id': self.project.id,
            'service_type': 'dj',
            'vendor_id': self.vendor_dj.id,
            'estimated_cost': 800.00,
        })
        
        # Trigger onchange
        assignment._onchange_vendor_id()
        
        self.assertEqual(assignment.vendor_contact, 'DJ Pro Services')
        
    def test_status_tracking(self):
        """Test assignment status workflow."""
        assignment = self.env['ptt.project.vendor.assignment'].create({
            'project_id': self.project.id,
            'service_type': 'dj',
            'vendor_id': self.vendor_dj.id,
            'estimated_cost': 800.00,
        })
        
        self.assertEqual(assignment.status, 'pending')
        
        assignment.status = 'confirmed'
        self.assertEqual(assignment.status, 'confirmed')
        
        assignment.status = 'completed'
        self.assertEqual(assignment.status, 'completed')
        
    def test_sql_constraints_positive_costs(self):
        """Test SQL constraints prevent negative costs."""
        from psycopg2 import IntegrityError
        
        # This should raise an integrity error due to negative cost
        with self.assertRaises(IntegrityError):
            with self.env.cr.savepoint():
                self.env['ptt.project.vendor.assignment'].create({
                    'project_id': self.project.id,
                    'service_type': 'dj',
                    'vendor_id': self.vendor_dj.id,
                    'estimated_cost': -100.00,
                })
