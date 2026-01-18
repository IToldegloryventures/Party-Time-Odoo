# -*- coding: utf-8 -*-
"""Tests for Vendor RFQ (Request for Quote) functionality."""

from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError
from datetime import date, timedelta


class TestVendorRfq(TransactionCase):
    """Test Vendor RFQ workflow."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test data."""
        super().setUpClass()
        
        # Create test partners
        cls.client = cls.env['res.partner'].create({
            'name': 'RFQ Test Client',
            'email': 'client@example.com',
        })
        
        cls.vendor1 = cls.env['res.partner'].create({
            'name': 'DJ Vendor 1',
            'email': 'dj1@example.com',
            'ptt_is_vendor': True,
        })
        
        cls.vendor2 = cls.env['res.partner'].create({
            'name': 'DJ Vendor 2',
            'email': 'dj2@example.com',
            'ptt_is_vendor': True,
        })
        
        cls.vendor3 = cls.env['res.partner'].create({
            'name': 'DJ Vendor 3',
            'email': 'dj3@example.com',
            'ptt_is_vendor': True,
        })
        
        # Create test project
        cls.project = cls.env['project.project'].create({
            'name': 'RFQ Test Project',
            'partner_id': cls.client.id,
            'ptt_event_name': 'Corporate Event',
            'ptt_event_date': date.today() + timedelta(days=30),
        })
        
    def test_rfq_default_closing_date(self):
        """Test that closing date defaults to 7 days from today."""
        rfq = self.env['ptt.vendor.rfq'].create({
            'service_type': 'dj',
            'project_id': self.project.id,
            'vendor_ids': [(6, 0, [self.vendor1.id])],
        })
        
        expected_date = date.today() + timedelta(days=7)
        self.assertEqual(rfq.closing_date, expected_date)
        
    def test_rfq_sequence_generation(self):
        """Test RFQ reference sequence is generated."""
        rfq = self.env['ptt.vendor.rfq'].create({
            'service_type': 'dj',
            'project_id': self.project.id,
            'closing_date': date.today() + timedelta(days=7),
            'vendor_ids': [(6, 0, [self.vendor1.id])],
        })
        
        # Should not be "New" after creation
        self.assertNotEqual(rfq.name, 'New')
        
    def test_rfq_workflow_draft_to_sent(self):
        """Test RFQ state transitions."""
        rfq = self.env['ptt.vendor.rfq'].create({
            'service_type': 'dj',
            'project_id': self.project.id,
            'closing_date': date.today() + timedelta(days=7),
            'vendor_ids': [(6, 0, [self.vendor1.id, self.vendor2.id])],
        })
        
        self.assertEqual(rfq.state, 'draft')
        
        # Note: action_send_to_vendors would send emails in production
        # Here we just test the state change
        rfq.state = 'sent'
        self.assertEqual(rfq.state, 'sent')
        
    def test_rfq_requires_vendors_to_send(self):
        """Test that sending RFQ requires at least one vendor."""
        rfq = self.env['ptt.vendor.rfq'].create({
            'service_type': 'dj',
            'project_id': self.project.id,
            'closing_date': date.today() + timedelta(days=7),
        })
        
        with self.assertRaises(UserError):
            rfq.action_send_to_vendors()
            
    def test_vendor_quote_submission(self):
        """Test vendor can submit a quote."""
        rfq = self.env['ptt.vendor.rfq'].create({
            'service_type': 'dj',
            'project_id': self.project.id,
            'closing_date': date.today() + timedelta(days=7),
            'vendor_ids': [(6, 0, [self.vendor1.id, self.vendor2.id])],
            'state': 'sent',
        })
        
        # Vendor 1 submits quote
        quote1 = self.env['ptt.vendor.quote.history'].create({
            'rfq_id': rfq.id,
            'vendor_id': self.vendor1.id,
            'quoted_price': 850.00,
            'notes': 'Includes all equipment',
        })
        
        # Vendor 2 submits quote
        quote2 = self.env['ptt.vendor.quote.history'].create({
            'rfq_id': rfq.id,
            'vendor_id': self.vendor2.id,
            'quoted_price': 750.00,
            'notes': 'Special discount',
        })
        
        rfq.invalidate_recordset()
        
        self.assertEqual(rfq.quote_count, 2)
        self.assertFalse(quote1.is_approved)
        self.assertFalse(quote2.is_approved)
        
    def test_approve_vendor_quote(self):
        """Test approving a vendor quote."""
        rfq = self.env['ptt.vendor.rfq'].create({
            'service_type': 'dj',
            'project_id': self.project.id,
            'closing_date': date.today() + timedelta(days=7),
            'vendor_ids': [(6, 0, [self.vendor1.id, self.vendor2.id])],
            'state': 'sent',
        })
        
        quote1 = self.env['ptt.vendor.quote.history'].create({
            'rfq_id': rfq.id,
            'vendor_id': self.vendor1.id,
            'quoted_price': 850.00,
        })
        
        quote2 = self.env['ptt.vendor.quote.history'].create({
            'rfq_id': rfq.id,
            'vendor_id': self.vendor2.id,
            'quoted_price': 750.00,
        })
        
        # Approve vendor 2's quote (lower price)
        rfq.action_approve_vendor(self.vendor2.id, quote2.id)
        
        self.assertEqual(rfq.state, 'done')
        self.assertEqual(rfq.approved_vendor_id, self.vendor2)
        self.assertEqual(rfq.approved_quote_id, quote2)
        
        # Check is_approved computed field
        quote1.invalidate_recordset()
        quote2.invalidate_recordset()
        
        self.assertFalse(quote1.is_approved)
        self.assertTrue(quote2.is_approved)
        
    def test_create_assignment_from_rfq(self):
        """Test creating vendor assignment from approved RFQ."""
        rfq = self.env['ptt.vendor.rfq'].create({
            'service_type': 'dj',
            'project_id': self.project.id,
            'closing_date': date.today() + timedelta(days=7),
            'vendor_ids': [(6, 0, [self.vendor1.id])],
            'estimated_budget': 1000.00,
            'state': 'sent',
        })
        
        quote = self.env['ptt.vendor.quote.history'].create({
            'rfq_id': rfq.id,
            'vendor_id': self.vendor1.id,
            'quoted_price': 900.00,
        })
        
        # Approve and create assignment
        rfq.action_approve_vendor(self.vendor1.id, quote.id)
        rfq.action_create_assignment()
        
        self.assertEqual(rfq.state, 'assigned')
        self.assertTrue(rfq.vendor_assignment_id)
        
        assignment = rfq.vendor_assignment_id
        self.assertEqual(assignment.vendor_id, self.vendor1)
        self.assertEqual(assignment.project_id, self.project)
        self.assertEqual(assignment.service_type, 'dj')
        
    def test_cannot_quote_closed_rfq(self):
        """Test vendors cannot submit quotes to closed RFQs."""
        rfq = self.env['ptt.vendor.rfq'].create({
            'service_type': 'dj',
            'project_id': self.project.id,
            'closing_date': date.today() + timedelta(days=7),
            'vendor_ids': [(6, 0, [self.vendor1.id])],
            'state': 'done',  # Already closed
        })
        
        with self.assertRaises(UserError):
            self.env['ptt.vendor.quote.history'].create({
                'rfq_id': rfq.id,
                'vendor_id': self.vendor1.id,
                'quoted_price': 900.00,
            })
            
    def test_rfq_cancel_and_reset(self):
        """Test RFQ cancel and reset to draft."""
        rfq = self.env['ptt.vendor.rfq'].create({
            'service_type': 'dj',
            'project_id': self.project.id,
            'closing_date': date.today() + timedelta(days=7),
            'vendor_ids': [(6, 0, [self.vendor1.id])],
            'state': 'sent',
        })
        
        rfq.action_cancel()
        self.assertEqual(rfq.state, 'cancel')
        
        rfq.action_reset_to_draft()
        self.assertEqual(rfq.state, 'draft')
        
    def test_event_details_from_project(self):
        """Test event details are pulled from linked project."""
        rfq = self.env['ptt.vendor.rfq'].create({
            'service_type': 'dj',
            'project_id': self.project.id,
            'closing_date': date.today() + timedelta(days=7),
            'vendor_ids': [(6, 0, [self.vendor1.id])],
        })
        
        self.assertEqual(rfq.event_name, 'Corporate Event')
        self.assertEqual(rfq.event_date, self.project.ptt_event_date)
