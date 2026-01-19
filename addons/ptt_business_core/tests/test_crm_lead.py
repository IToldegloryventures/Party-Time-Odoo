# -*- coding: utf-8 -*-
"""Tests for CRM Lead to Project flow."""

from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError


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
            'ptt_is_vendor': True,
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
            'x_studio_event_name': 'Annual Company Gala',
            'x_studio_event_date': '2026-06-15',
            'ptt_guest_count': 200,
            'x_studio_venue_name': 'Grand Ballroom',
            'ptt_service_dj': True,
            'ptt_service_photovideo': True,
        })
        
        self.assertEqual(lead.x_studio_event_name, 'Annual Company Gala')
        self.assertEqual(lead.ptt_guest_count, 200)
        self.assertTrue(lead.ptt_service_dj)
        self.assertTrue(lead.ptt_service_photovideo)
        self.assertFalse(lead.ptt_service_lighting)
        
    def test_crm_lead_vendor_estimates(self):
        """Test adding vendor estimates to a lead."""
        lead = self.env['crm.lead'].create({
            'name': 'Wedding Reception',
            'partner_id': self.partner.id,
            'x_studio_event_name': 'Smith-Jones Wedding',
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
        
    def test_create_project_from_lead(self):
        """Test creating a project from a CRM lead."""
        lead = self.env['crm.lead'].create({
            'name': 'Birthday Celebration',
            'partner_id': self.partner.id,
            'user_id': self.user.id,
            'x_studio_event_name': 'John\'s 50th Birthday',
            'x_studio_event_date': '2026-08-20',
            'ptt_guest_count': 75,
            'x_studio_venue_name': 'Country Club',
            'x_studio_venue_address': '123 Golf Drive',
            'ptt_location_type': 'indoor',
        })
        
        # Create project from lead
        lead.action_create_project()
        
        # Verify project was created
        self.assertTrue(lead.ptt_project_id)
        project = lead.ptt_project_id
        
        self.assertEqual(project.partner_id, self.partner)
        self.assertEqual(project.ptt_crm_lead_id, lead)
        self.assertEqual(project.x_studio_event_name, 'John\'s 50th Birthday')
        self.assertEqual(project.ptt_guest_count, 75)
        self.assertEqual(project.x_studio_venue_name, 'Country Club')
        
    def test_cannot_create_duplicate_project(self):
        """Test that a second project cannot be created for same lead."""
        lead = self.env['crm.lead'].create({
            'name': 'Test Event',
            'partner_id': self.partner.id,
            'user_id': self.user.id,
            'x_studio_event_name': 'Duplicate Test',
        })
        
        # Create first project
        lead.action_create_project()
        self.assertTrue(lead.ptt_project_id)
        
        # Attempt to create second project should fail
        with self.assertRaises(UserError):
            lead.action_create_project()
            
    def test_lead_requires_partner_for_project(self):
        """Test that project creation requires a partner."""
        lead = self.env['crm.lead'].create({
            'name': 'No Partner Event',
            'user_id': self.user.id,
            'x_studio_event_name': 'Partner Required Test',
        })
        
        # Attempt to create project without partner should fail
        with self.assertRaises(UserError):
            lead.action_create_project()
            
    def test_project_count_computed(self):
        """Test project count field is computed correctly."""
        lead = self.env['crm.lead'].create({
            'name': 'Count Test',
            'partner_id': self.partner.id,
            'user_id': self.user.id,
        })
        
        # Initially no project
        self.assertEqual(lead.ptt_project_count, 0)
        
        # Create project
        lead.action_create_project()
        lead.invalidate_recordset()
        
        # Now should be 1
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
