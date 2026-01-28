# -*- coding: utf-8 -*-
"""Tests for Project Vendor Assignment in ptt_project_management."""

from odoo.tests.common import TransactionCase, tagged


@tagged('standard', 'at_install')
class TestProjectVendorAssignment(TransactionCase):
    """Test Project Vendor Assignment functionality."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test data."""
        super().setUpClass()
        
        # Create test project
        cls.project = cls.env['project.project'].create({
            'name': 'Assignment Test Event',
            'partner_id': cls.env['res.partner'].create({
                'name': 'Test Customer',
                'email': 'customer@example.com',
            }).id,
        })
        
        # Create test vendor
        cls.vendor = cls.env['res.partner'].create({
            'name': 'Test Vendor',
            'email': 'vendor@example.com',
            'supplier_rank': 1,
        })
    
    def test_vendor_assignment_creation(self):
        """Test creating a vendor assignment."""
        assignment = self.env['ptt.project.vendor.assignment'].create({
            'project_id': self.project.id,
            'vendor_id': self.vendor.id,
            'service_type': 'dj',
            'estimated_cost': 1000.0,
        })
        
        self.assertEqual(assignment.project_id, self.project)
        self.assertEqual(assignment.vendor_id, self.vendor)
        self.assertEqual(assignment.service_type, 'dj')
        self.assertEqual(assignment.estimated_cost, 1000.0)
        self.assertEqual(assignment.status, 'pending')
    
    def test_vendor_assignment_status_workflow(self):
        """Test vendor assignment status workflow."""
        assignment = self.env['ptt.project.vendor.assignment'].create({
            'project_id': self.project.id,
            'vendor_id': self.vendor.id,
            'service_type': 'photography',
            'status': 'pending',
        })
        
        # Accept assignment
        assignment.action_vendor_accept()
        self.assertEqual(assignment.status, 'confirmed')
        
        # Complete assignment
        assignment.action_complete()
        self.assertEqual(assignment.status, 'completed')
    
    def test_vendor_assignment_cost_tracking(self):
        """Test cost tracking on vendor assignment."""
        assignment = self.env['ptt.project.vendor.assignment'].create({
            'project_id': self.project.id,
            'vendor_id': self.vendor.id,
            'service_type': 'lighting',
            'estimated_cost': 500.0,
        })
        
        # Update actual cost
        assignment.write({'actual_cost': 450.0})
        
        # Check variance (if computed)
        assignment.invalidate_recordset()
        # Variance should be -50.0 (saved money)
    
    def test_vendor_assignment_access_token(self):
        """Test access token generation for portal access."""
        assignment = self.env['ptt.project.vendor.assignment'].create({
            'project_id': self.project.id,
            'vendor_id': self.vendor.id,
            'service_type': 'dj',
        })
        
        # Access token should be generated
        self.assertTrue(assignment.access_token)
        self.assertIsInstance(assignment.access_token, str)
        self.assertEqual(len(assignment.access_token), 16)  # Standard token length
