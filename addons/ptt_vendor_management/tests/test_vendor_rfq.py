# -*- coding: utf-8 -*-
"""Tests for Vendor RFQ (Request for Quote) system."""

from datetime import timedelta
from odoo import fields
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import UserError, ValidationError


@tagged('standard', 'at_install')
class TestVendorRFQ(TransactionCase):
    """Test Vendor RFQ model and workflow."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test data."""
        super().setUpClass()
        
        # Create test partners
        cls.customer = cls.env['res.partner'].create({
            'name': 'RFQ Test Customer',
            'email': 'customer@example.com',
            'is_company': True,
        })
        
        cls.vendor1 = cls.env['res.partner'].create({
            'name': 'Vendor One',
            'email': 'vendor1@example.com',
            'supplier_rank': 1,
            'is_company': True,
        })
        
        cls.vendor2 = cls.env['res.partner'].create({
            'name': 'Vendor Two',
            'email': 'vendor2@example.com',
            'supplier_rank': 1,
            'is_company': True,
        })
        
        # Create test project
        cls.project = cls.env['project.project'].create({
            'name': 'RFQ Test Event',
            'partner_id': cls.customer.id,
            'ptt_event_date': fields.Date.today() + timedelta(days=30),
        })
        
        # Create test product
        cls.product = cls.env['product.product'].create({
            'name': 'Test Service',
            'type': 'service',
            'list_price': 1000.0,
        })
        
        # Create currency
        cls.currency = cls.env.company.currency_id
    
    def test_rfq_creation(self):
        """Test creating an RFQ."""
        rfq = self.env['ptt.vendor.rfq'].create({
            'name': 'RFQ-001',
            'project_id': self.project.id,
            'product_id': self.product.id,
            'description': 'Test RFQ description',
            'quantity': 1.0,
            'vendor_ids': [(6, 0, [self.vendor1.id, self.vendor2.id])],
            'closing_date': fields.Date.today() + timedelta(days=7),
        })
        
        self.assertEqual(rfq.name, 'RFQ-001')
        self.assertEqual(rfq.state, 'draft')
        self.assertEqual(len(rfq.vendor_ids), 2)
        self.assertEqual(rfq.customer_id, self.customer)
        self.assertEqual(rfq.event_date, self.project.ptt_event_date)
    
    def test_rfq_send(self):
        """Test sending RFQ to vendors."""
        rfq = self.env['ptt.vendor.rfq'].create({
            'name': 'RFQ-002',
            'project_id': self.project.id,
            'product_id': self.product.id,
            'vendor_ids': [(6, 0, [self.vendor1.id])],
            'closing_date': fields.Date.today() + timedelta(days=7),
        })
        
        self.assertEqual(rfq.state, 'draft')
        
        # Send RFQ
        rfq.action_send_rfq()
        
        self.assertEqual(rfq.state, 'in_progress')
        self.assertTrue(rfq.send_date)
    
    def test_rfq_quote_submission(self):
        """Test vendor quote submission."""
        rfq = self.env['ptt.vendor.rfq'].create({
            'name': 'RFQ-003',
            'project_id': self.project.id,
            'product_id': self.product.id,
            'vendor_ids': [(6, 0, [self.vendor1.id])],
            'closing_date': fields.Date.today() + timedelta(days=7),
            'state': 'in_progress',
        })
        
        # Submit quote from vendor1
        quote = self.env['ptt.vendor.quote.history'].create({
            'rfq_id': rfq.id,
            'vendor_id': self.vendor1.id,
            'quoted_price': 950.0,
            'currency_id': self.currency.id,
        })
        
        self.assertEqual(quote.quoted_price, 950.0)
        self.assertEqual(quote.vendor_id, self.vendor1)
        self.assertIn(quote, rfq.quote_history_ids)
        self.assertEqual(rfq.quote_count, 1)
    
    def test_rfq_winner_selection(self):
        """Test selecting a winner for RFQ."""
        rfq = self.env['ptt.vendor.rfq'].create({
            'name': 'RFQ-004',
            'project_id': self.project.id,
            'product_id': self.product.id,
            'vendor_ids': [(6, 0, [self.vendor1.id, self.vendor2.id])],
            'closing_date': fields.Date.today() + timedelta(days=7),
            'state': 'in_progress',
        })
        
        # Create quotes from both vendors
        quote1 = self.env['ptt.vendor.quote.history'].create({
            'rfq_id': rfq.id,
            'vendor_id': self.vendor1.id,
            'quoted_price': 900.0,
            'currency_id': self.currency.id,
        })
        
        quote2 = self.env['ptt.vendor.quote.history'].create({
            'rfq_id': rfq.id,
            'vendor_id': self.vendor2.id,
            'quoted_price': 850.0,
            'currency_id': self.currency.id,
        })
        
        # Select winner
        rfq.winner_quote_id = quote2.id
        rfq.action_select_winner()
        
        self.assertEqual(rfq.state, 'done')
        self.assertEqual(rfq.winner_quote_id, quote2)
        self.assertEqual(quote2.is_winner, True)
        self.assertEqual(quote1.is_winner, False)
    
    def test_rfq_close_automatically(self):
        """Test RFQ auto-closes on closing date."""
        rfq = self.env['ptt.vendor.rfq'].create({
            'name': 'RFQ-005',
            'project_id': self.project.id,
            'product_id': self.product.id,
            'vendor_ids': [(6, 0, [self.vendor1.id])],
            'closing_date': fields.Date.today() - timedelta(days=1),  # Past date
            'state': 'in_progress',
        })
        
        # Run the cron to close expired RFQs
        self.env['ptt.vendor.rfq'].cron_close_expired_rfqs()
        
        rfq.invalidate_recordset()
        self.assertEqual(rfq.state, 'closed')
    
    def test_rfq_requires_vendors(self):
        """Test RFQ requires at least one vendor."""
        with self.assertRaises(ValidationError):
            self.env['ptt.vendor.rfq'].create({
                'name': 'RFQ-006',
                'project_id': self.project.id,
                'product_id': self.product.id,
                'vendor_ids': [(5, 0, 0)],  # Empty list
                'closing_date': fields.Date.today() + timedelta(days=7),
            })
    
    def test_rfq_quote_count_computed(self):
        """Test quote count is computed correctly."""
        rfq = self.env['ptt.vendor.rfq'].create({
            'name': 'RFQ-007',
            'project_id': self.project.id,
            'product_id': self.product.id,
            'vendor_ids': [(6, 0, [self.vendor1.id, self.vendor2.id])],
            'closing_date': fields.Date.today() + timedelta(days=7),
            'state': 'in_progress',
        })
        
        self.assertEqual(rfq.quote_count, 0)
        
        # Add quotes
        self.env['ptt.vendor.quote.history'].create({
            'rfq_id': rfq.id,
            'vendor_id': self.vendor1.id,
            'quoted_price': 1000.0,
            'currency_id': self.currency.id,
        })
        
        self.env['ptt.vendor.quote.history'].create({
            'rfq_id': rfq.id,
            'vendor_id': self.vendor2.id,
            'quoted_price': 1100.0,
            'currency_id': self.currency.id,
        })
        
        rfq.invalidate_recordset()
        self.assertEqual(rfq.quote_count, 2)
