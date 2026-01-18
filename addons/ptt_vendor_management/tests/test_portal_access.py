# -*- coding: utf-8 -*-
"""Tests for portal access security."""

from odoo.tests.common import TransactionCase
from datetime import datetime, timedelta


class TestPortalAccessSecurity(TransactionCase):
    """Test portal access token security and vendor isolation."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test data."""
        super().setUpClass()
        
        # Create test partners
        cls.client = cls.env['res.partner'].create({
            'name': 'Portal Test Client',
            'email': 'client@example.com',
        })
        
        cls.vendor1 = cls.env['res.partner'].create({
            'name': 'Vendor Alpha',
            'email': 'alpha@vendor.com',
            'ptt_is_vendor': True,
            'ptt_vendor_portal_access': True,
        })
        
        cls.vendor2 = cls.env['res.partner'].create({
            'name': 'Vendor Beta',
            'email': 'beta@vendor.com',
            'ptt_is_vendor': True,
            'ptt_vendor_portal_access': True,
        })
        
        # Create test project
        cls.project = cls.env['project.project'].create({
            'name': 'Portal Test Project',
            'partner_id': cls.client.id,
        })
        
    def test_access_token_generation(self):
        """Test access token is generated correctly."""
        assignment = self.env['ptt.project.vendor.assignment'].create({
            'project_id': self.project.id,
            'service_type': 'dj',
            'vendor_id': self.vendor1.id,
            'estimated_cost': 1000.00,
        })
        
        # Initially no token
        self.assertFalse(assignment.access_token)
        
        # Generate token
        token = assignment._generate_access_token()
        
        self.assertTrue(token)
        self.assertEqual(len(token), 43)  # Base64 URL-safe token length
        self.assertEqual(assignment.access_token, token)
        
    def test_access_token_expiration(self):
        """Test access token expires after configured days."""
        assignment = self.env['ptt.project.vendor.assignment'].create({
            'project_id': self.project.id,
            'service_type': 'dj',
            'vendor_id': self.vendor1.id,
            'estimated_cost': 1000.00,
        })
        
        # Generate token with default expiry (30 days)
        token = assignment._generate_access_token()
        
        # Token should be valid now
        self.assertTrue(assignment._is_token_valid(token))
        
        # Token expiry should be ~30 days from now
        self.assertTrue(assignment.access_token_expires)
        days_until_expiry = (assignment.access_token_expires - datetime.now()).days
        self.assertGreaterEqual(days_until_expiry, 29)
        self.assertLessEqual(days_until_expiry, 31)
        
    def test_access_token_custom_expiry(self):
        """Test access token with custom expiry."""
        assignment = self.env['ptt.project.vendor.assignment'].create({
            'project_id': self.project.id,
            'service_type': 'dj',
            'vendor_id': self.vendor1.id,
            'estimated_cost': 1000.00,
        })
        
        # Generate token with 7 day expiry
        assignment._generate_access_token(expiry_days=7)
        
        days_until_expiry = (assignment.access_token_expires - datetime.now()).days
        self.assertGreaterEqual(days_until_expiry, 6)
        self.assertLessEqual(days_until_expiry, 8)
        
    def test_expired_token_invalid(self):
        """Test expired token is rejected."""
        assignment = self.env['ptt.project.vendor.assignment'].create({
            'project_id': self.project.id,
            'service_type': 'dj',
            'vendor_id': self.vendor1.id,
            'estimated_cost': 1000.00,
        })
        
        token = assignment._generate_access_token()
        
        # Manually set expiry to past
        assignment.access_token_expires = datetime.now() - timedelta(days=1)
        
        # Token should now be invalid
        self.assertFalse(assignment._is_token_valid(token))
        
    def test_wrong_token_invalid(self):
        """Test wrong token is rejected."""
        assignment = self.env['ptt.project.vendor.assignment'].create({
            'project_id': self.project.id,
            'service_type': 'dj',
            'vendor_id': self.vendor1.id,
            'estimated_cost': 1000.00,
        })
        
        assignment._generate_access_token()
        
        # Wrong token should be invalid
        self.assertFalse(assignment._is_token_valid('wrong_token'))
        self.assertFalse(assignment._is_token_valid(''))
        self.assertFalse(assignment._is_token_valid(None))
        
    def test_vendor_confirmation_workflow(self):
        """Test vendor can confirm assignment via portal."""
        assignment = self.env['ptt.project.vendor.assignment'].create({
            'project_id': self.project.id,
            'service_type': 'dj',
            'vendor_id': self.vendor1.id,
            'estimated_cost': 1000.00,
        })
        
        self.assertFalse(assignment.vendor_confirmed)
        self.assertEqual(assignment.status, 'pending')
        
        # Vendor confirms
        assignment.action_vendor_confirm()
        
        self.assertTrue(assignment.vendor_confirmed)
        self.assertEqual(assignment.status, 'confirmed')
        self.assertTrue(assignment.vendor_confirmed_date)
        
    def test_vendor_decline_workflow(self):
        """Test vendor can decline assignment."""
        assignment = self.env['ptt.project.vendor.assignment'].create({
            'project_id': self.project.id,
            'service_type': 'dj',
            'vendor_id': self.vendor1.id,
            'estimated_cost': 1000.00,
        })
        
        assignment.action_vendor_decline()
        
        self.assertFalse(assignment.vendor_confirmed)
        self.assertEqual(assignment.status, 'cancelled')
        
    def test_portal_assignment_filtering(self):
        """Test portal assignments exclude cancelled."""
        # Create assignments for vendor1
        assignment1 = self.env['ptt.project.vendor.assignment'].create({
            'project_id': self.project.id,
            'service_type': 'dj',
            'vendor_id': self.vendor1.id,
            'estimated_cost': 1000.00,
            'status': 'confirmed',
        })
        
        assignment2 = self.env['ptt.project.vendor.assignment'].create({
            'project_id': self.project.id,
            'service_type': 'photovideo',
            'vendor_id': self.vendor1.id,
            'estimated_cost': 1500.00,
            'status': 'cancelled',
        })
        
        assignment3 = self.env['ptt.project.vendor.assignment'].create({
            'project_id': self.project.id,
            'service_type': 'lighting',
            'vendor_id': self.vendor1.id,
            'estimated_cost': 500.00,
            'status': 'pending',
        })
        
        self.vendor1.invalidate_recordset()
        
        # Portal assignments should exclude cancelled
        portal_assignments = self.vendor1.ptt_portal_assignment_ids
        
        self.assertIn(assignment1, portal_assignments)
        self.assertNotIn(assignment2, portal_assignments)
        self.assertIn(assignment3, portal_assignments)
        
        # Active count should be 2 (confirmed + pending)
        self.assertEqual(self.vendor1.ptt_active_assignment_count, 2)
        
    def test_vendor_isolation(self):
        """Test vendors only see their own assignments in portal view."""
        # Create assignment for vendor1
        assignment1 = self.env['ptt.project.vendor.assignment'].create({
            'project_id': self.project.id,
            'service_type': 'dj',
            'vendor_id': self.vendor1.id,
            'estimated_cost': 1000.00,
        })
        
        # Create assignment for vendor2
        assignment2 = self.env['ptt.project.vendor.assignment'].create({
            'project_id': self.project.id,
            'service_type': 'photovideo',
            'vendor_id': self.vendor2.id,
            'estimated_cost': 1500.00,
        })
        
        self.vendor1.invalidate_recordset()
        self.vendor2.invalidate_recordset()
        
        # Vendor1 should only see their assignments
        vendor1_assignments = self.vendor1.ptt_portal_assignment_ids
        self.assertIn(assignment1, vendor1_assignments)
        self.assertNotIn(assignment2, vendor1_assignments)
        
        # Vendor2 should only see their assignments
        vendor2_assignments = self.vendor2.ptt_portal_assignment_ids
        self.assertNotIn(assignment1, vendor2_assignments)
        self.assertIn(assignment2, vendor2_assignments)
        
    def test_document_count(self):
        """Test document count is computed correctly."""
        assignment = self.env['ptt.project.vendor.assignment'].create({
            'project_id': self.project.id,
            'service_type': 'dj',
            'vendor_id': self.vendor1.id,
            'estimated_cost': 1000.00,
        })
        
        self.assertEqual(assignment.document_count, 0)
        
        # Add documents
        self.env['ptt.vendor.document'].create({
            'vendor_assignment_id': assignment.id,
            'name': 'Contract',
        })
        
        self.env['ptt.vendor.document'].create({
            'vendor_assignment_id': assignment.id,
            'name': 'Invoice',
        })
        
        assignment.invalidate_recordset()
        
        self.assertEqual(assignment.document_count, 2)
