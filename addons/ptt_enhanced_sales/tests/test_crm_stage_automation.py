# -*- coding: utf-8 -*-
"""Tests for CRM Stage Automation feature.

Feature 1: CRM Stage Automation
- Auto-updates CRM when quote sent/confirmed
- Links CRM ↔ Project properly
"""

from odoo.tests.common import TransactionCase, tagged


@tagged('standard', 'at_install')
class TestCrmStageAutomation(TransactionCase):
    """Test CRM stage automation when quotes are sent/confirmed."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test data."""
        super().setUpClass()
        
        # Create test partner
        cls.partner = cls.env['res.partner'].create({
            'name': 'CRM Automation Test Client',
            'email': 'automation@example.com',
        })
        
        # Create test user
        cls.user = cls.env['res.users'].create({
            'name': 'Test Sales Rep',
            'login': 'test_crm_automation',
            'email': 'sales@example.com',
        })
        
        # Find or create CRM stages
        cls.stage_new = cls.env['crm.stage'].search([
            ('name', 'ilike', 'New'),
        ], limit=1)
        if not cls.stage_new:
            cls.stage_new = cls.env['crm.stage'].create({
                'name': 'New',
                'sequence': 10,
            })

        cls.stage_proposal = cls.env.ref(
            'ptt_business_core.stage_ptt_proposal_sent',
            raise_if_not_found=False,
        )
        if not cls.stage_proposal:
            cls.stage_proposal = cls.env['crm.stage'].create({
                'name': 'Proposal Sent',
                'sequence': 30,
            })

        cls.stage_contract = cls.env.ref(
            'ptt_business_core.stage_ptt_contract_sent',
            raise_if_not_found=False,
        )
        if not cls.stage_contract:
            cls.stage_contract = cls.env['crm.stage'].create({
                'name': 'Contract Sent',
                'sequence': 50,
            })

        cls.stage_booked = cls.env.ref(
            'crm.stage_lead4',  # Booked stage (was Won, renamed)
            raise_if_not_found=False,
        )
        if not cls.stage_booked:
            cls.stage_booked = cls.env['crm.stage'].create({
                'name': 'Booked',
                'sequence': 70,
                'is_won': True,
            })

        cls.stage_won = cls.env['crm.stage'].search([
            ('is_won', '=', True),
        ], limit=1)
        if not cls.stage_won:
            cls.stage_won = cls.env['crm.stage'].create({
                'name': 'Won',
                'sequence': 100,
                'is_won': True,
            })
    
    def test_quote_sent_updates_crm_stage(self):
        """Test that sending a quote updates CRM to Proposal stage."""
        # Create CRM lead
        lead = self.env['crm.lead'].create({
            'name': 'Test Opportunity',
            'partner_id': self.partner.id,
            'user_id': self.user.id,
            'stage_id': self.stage_new.id,
            'ptt_event_name': 'Corporate Gala',
        })
        
        self.assertEqual(lead.stage_id, self.stage_new)
        self.assertFalse(lead.ptt_proposal_sent)
        
        # Create quote linked to lead
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'opportunity_id': lead.id,
            'event_name': 'Corporate Gala',
        })
        
        # Simulate sending quote
        order.action_quotation_sent()
        
        # Lead should have proposal_sent marked
        self.assertTrue(lead.ptt_proposal_sent)
        self.assertEqual(lead.stage_id, self.stage_proposal)
        
    def test_order_confirmed_marks_crm_won(self):
        """Test that confirming order marks CRM as Won."""
        # Create CRM lead
        lead = self.env['crm.lead'].create({
            'name': 'Win Test Opportunity',
            'partner_id': self.partner.id,
            'user_id': self.user.id,
            'stage_id': self.stage_proposal.id,
        })
        
        self.assertLess(lead.probability, 100)
        
        # Create and confirm quote
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'opportunity_id': lead.id,
            'order_line': [(0, 0, {
                'name': 'DJ Services',
                'product_uom_qty': 4,
                'price_unit': 300,
            })],
        })
        
        # Need a product for order line - use generic service
        product = self.env['product.product'].create({
            'name': 'Test DJ Service',
            'type': 'service',
            'list_price': 300,
        })
        order.order_line.product_id = product
        
        order.action_confirm()
        
        # Lead should be marked as won
        lead.invalidate_recordset()
        self.assertEqual(lead.probability, 100)
        self.assertTrue(lead.stage_id.is_won)
        
    def test_no_lead_no_error(self):
        """Test that orders without leads don't cause errors."""
        # Create order without lead
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'event_name': 'Standalone Event',
        })
        
        # These should not raise errors
        order._update_crm_stage_on_quote_sent()
        order._update_crm_stage_on_order_confirmed()
        
    def test_sync_crm_from_order(self):
        """Test syncing event details from order to CRM."""
        # Create CRM lead without event details
        lead = self.env['crm.lead'].create({
            'name': 'Sync Test Opportunity',
            'partner_id': self.partner.id,
            'user_id': self.user.id,
        })
        
        self.assertFalse(lead.ptt_event_name)
        
        # Create order with event details
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'opportunity_id': lead.id,
            'event_name': 'Wedding Reception',
            'event_guest_count': 150,
            'event_venue': 'Grand Ballroom',
        })
        
        # Sync from order to lead
        order._sync_crm_lead_from_order()
        
        lead.invalidate_recordset()
        self.assertEqual(lead.ptt_event_name, 'Wedding Reception')
        self.assertEqual(lead.ptt_guest_count, 150)
        self.assertEqual(lead.ptt_venue_name, 'Grand Ballroom')
    
    def test_contract_sent_updates_crm_stage(self):
        """Test that sending a contract updates CRM to Contract Sent stage."""
        # Create CRM lead at Proposal stage
        lead = self.env['crm.lead'].create({
            'name': 'Contract Test Opportunity',
            'partner_id': self.partner.id,
            'user_id': self.user.id,
            'stage_id': self.stage_proposal.id,
            'ptt_proposal_sent': True,
        })
        
        self.assertFalse(lead.ptt_contract_sent)
        
        # Create quote linked to lead
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'opportunity_id': lead.id,
            'event_name': 'Contract Test Event',
        })
        
        # Simulate sending contract
        order.action_send_contract()
        
        # Lead should have contract_sent marked
        lead.invalidate_recordset()
        self.assertTrue(lead.ptt_contract_sent)
        self.assertEqual(lead.stage_id, self.stage_contract)
        
    def test_booked_stage_on_confirmation(self):
        """Test that order confirmation moves CRM to Booked stage."""
        # Create CRM lead at Contract stage
        lead = self.env['crm.lead'].create({
            'name': 'Booking Test Opportunity',
            'partner_id': self.partner.id,
            'user_id': self.user.id,
            'ptt_contract_sent': True,
        })
        
        self.assertFalse(lead.ptt_booked)
        
        # Create product and order
        product = self.env['product.product'].create({
            'name': 'Test Booking Service',
            'type': 'service',
            'list_price': 500,
        })
        
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'opportunity_id': lead.id,
            'order_line': [(0, 0, {
                'product_id': product.id,
                'product_uom_qty': 4,
                'price_unit': 500,
            })],
        })
        
        # Confirm order then simulate payment confirmation
        order.action_confirm()
        order._update_crm_stage_on_payment_confirmed(force=True)
        
        # Lead should be booked
        lead.invalidate_recordset()
        self.assertTrue(lead.ptt_booked)
        self.assertEqual(lead.probability, 100)
        
    def test_already_won_lead_not_changed(self):
        """Test that already-won leads aren't modified again."""
        # Create already-won lead
        lead = self.env['crm.lead'].create({
            'name': 'Already Won Opportunity',
            'partner_id': self.partner.id,
            'user_id': self.user.id,
            'stage_id': self.stage_won.id,
            'probability': 100,
        })
        
        original_stage = lead.stage_id
        
        # Create and confirm order
        product = self.env['product.product'].create({
            'name': 'Test Service',
            'type': 'service',
            'list_price': 100,
        })
        
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'opportunity_id': lead.id,
            'order_line': [(0, 0, {
                'product_id': product.id,
                'product_uom_qty': 1,
                'price_unit': 100,
            })],
        })
        
        order.action_confirm()
        
        # Stage should remain the same (already won)
        lead.invalidate_recordset()
        self.assertEqual(lead.stage_id, original_stage)
        self.assertEqual(lead.probability, 100)


@tagged('standard', 'at_install')
class TestCrmProjectLink(TransactionCase):
    """Test CRM ↔ Project linking functionality."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test data."""
        super().setUpClass()
        
        cls.partner = cls.env['res.partner'].create({
            'name': 'Project Link Test Client',
            'email': 'projectlink@example.com',
        })
        
        cls.user = cls.env['res.users'].create({
            'name': 'Test PM',
            'login': 'test_project_link',
            'email': 'pm@example.com',
        })
    
    def test_crm_to_project_link(self):
        """Test project creation from CRM maintains link."""
        lead = self.env['crm.lead'].create({
            'name': 'Project Link Test',
            'partner_id': self.partner.id,
            'user_id': self.user.id,
            'ptt_event_name': 'Linked Event',
            'ptt_guest_count': 100,
        })
        
        # Create project from lead
        lead.action_create_project()
        
        # Verify bidirectional link
        self.assertTrue(lead.ptt_project_id)
        project = lead.ptt_project_id
        
        self.assertEqual(project.ptt_crm_lead_id, lead)
        self.assertEqual(project.ptt_event_name, 'Linked Event')
        
    def test_sale_order_project_event_details(self):
        """Test project created from sale order gets event details."""
        lead = self.env['crm.lead'].create({
            'name': 'SO Project Test',
            'partner_id': self.partner.id,
            'user_id': self.user.id,
        })
        
        # Create sale order with event details
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'opportunity_id': lead.id,
            'event_name': 'Wedding Event',
            'event_guest_count': 200,
            'event_venue': 'Country Club',
            'event_duration': 6.0,
        })
        
        # Create project directly
        project = self.env['project.project'].create({
            'name': 'Test Project',
            'partner_id': self.partner.id,
        })
        
        # Apply event details
        order._apply_event_details_to_project(project)
        
        self.assertEqual(project.ptt_event_name, 'Wedding Event')
        self.assertEqual(project.ptt_guest_count, 200)
        self.assertEqual(project.ptt_venue_name, 'Country Club')
        self.assertEqual(project.ptt_total_hours, 6.0)
