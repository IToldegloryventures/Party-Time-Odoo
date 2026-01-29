# -*- coding: utf-8 -*-
"""Tests for CRM Lead to Project flow."""

from odoo.tests.common import TransactionCase, tagged


@tagged('standard', 'at_install')
class TestCrmLeadProjectFlow(TransactionCase):
    """Test CRM Lead extensions and project creation flow."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test data."""
        super().setUpClass()
        
        # Create a test partner (customer)
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Event Client',
            'email': 'client@example.com',
            'phone': '555-1234',
        })
        
        # Create a test vendor partner
        cls.vendor = cls.env['res.partner'].create({
            'name': 'Test DJ Vendor',
            'email': 'dj@example.com',
            'supplier_rank': 1,
        })
        
        # Create a test user
        cls.user = cls.env['res.users'].create({
            'name': 'Test Sales Rep',
            'login': 'test_sales_rep',
            'email': 'sales@example.com',
        })
        
    def test_crm_lead_creation_with_event_details(self):
        """Test creating a CRM lead with PTT event fields."""
        lead = self.env['crm.lead'].create({
            'name': 'Corporate Annual Gala',
            'partner_id': self.partner.id,
            'user_id': self.user.id,
            'ptt_event_name': 'Annual Company Gala',
            'ptt_event_date': '2026-06-15',
            'ptt_guest_count': 200,
            'ptt_venue_name': 'Grand Ballroom',
        })
        
        self.assertEqual(lead.ptt_event_name, 'Annual Company Gala')
        self.assertEqual(lead.ptt_guest_count, 200)
        
    def test_crm_lead_vendor_estimates(self):
        """Test adding vendor estimates to a lead."""
        lead = self.env['crm.lead'].create({
            'name': 'Wedding Reception',
            'partner_id': self.partner.id,
            'ptt_event_name': 'Smith-Jones Wedding',
            'ptt_estimated_client_total': 5000.00,
        })
        
        # Add vendor estimates
        self.env['ptt.crm.vendor.estimate'].create({
            'crm_lead_id': lead.id,
            'service_type': 'dj',
            'vendor_name': 'DJ Pro Services',
            'estimated_cost': 800.00,
        })
        
        self.env['ptt.crm.vendor.estimate'].create({
            'crm_lead_id': lead.id,
            'service_type': 'photography',
            'vendor_name': 'Photo Magic',
            'estimated_cost': 1200.00,
        })
        
        # Trigger recompute
        lead.invalidate_recordset()
        
        self.assertEqual(lead.ptt_estimated_vendor_total, 2000.00)
        self.assertEqual(lead.ptt_estimated_margin, 3000.00)
        self.assertEqual(lead.ptt_margin_percent, 60.0)
        
    def test_project_link_from_crm(self):
        """Test that project created from SO gets linked to CRM lead.
        
        The actual workflow is:
        1. CRM Lead exists with event details
        2. Sale Order is created from the lead (via quotation template)
        3. SO includes 'Event Kickoff' product which creates project
        4. When SO is confirmed, project is linked back to CRM lead
        
        This test verifies the bidirectional link works correctly.
        """
        lead = self.env['crm.lead'].create({
            'name': 'Birthday Celebration',
            'partner_id': self.partner.id,
            'user_id': self.user.id,
            'ptt_event_name': 'John\'s 50th Birthday',
            'ptt_event_date': '2026-08-20',
            'ptt_guest_count': 75,
            'ptt_venue_name': 'Country Club',
            'ptt_venue_address': '123 Golf Drive',
            'ptt_location_type': 'indoor',
        })
        
        # Initially no project linked
        self.assertFalse(lead.ptt_project_id)
        self.assertEqual(lead.ptt_project_count, 0)
        
        # Create a project and manually link it (simulating what SO confirmation does)
        project = self.env['project.project'].create({
            'name': 'Birthday Celebration Project',
            'partner_id': self.partner.id,
            'ptt_crm_lead_id': lead.id,
        })
        
        # Link project to lead (simulating _ptt_link_crm_to_projects)
        lead.ptt_project_id = project.id
        
        # Verify bidirectional link
        self.assertEqual(project.ptt_crm_lead_id, lead)
        self.assertEqual(lead.ptt_project_id, project)
        
        # Verify event details flow to project via related fields
        self.assertEqual(project.ptt_event_name, 'John\'s 50th Birthday')
        self.assertEqual(project.ptt_guest_count, 75)
        self.assertEqual(project.ptt_venue_name, 'Country Club')
        
        # Project count should update
        lead.invalidate_recordset()
        self.assertEqual(lead.ptt_project_count, 1)
        
    def test_vendor_estimates_cascade_delete(self):
        """Test that vendor estimates are deleted when lead is deleted."""
        lead = self.env['crm.lead'].create({
            'name': 'Cascade Delete Test',
            'partner_id': self.partner.id,
        })
        
        estimate = self.env['ptt.crm.vendor.estimate'].create({
            'crm_lead_id': lead.id,
            'service_type': 'dj',
            'estimated_cost': 500.00,
        })
        
        estimate_id = estimate.id
        
        # Delete lead
        lead.unlink()
        
        # Estimate should be deleted too
        self.assertFalse(self.env['ptt.crm.vendor.estimate'].browse(estimate_id).exists())
