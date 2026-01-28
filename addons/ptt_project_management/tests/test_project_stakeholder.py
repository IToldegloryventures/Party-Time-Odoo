# -*- coding: utf-8 -*-
"""Tests for Project Stakeholder model."""

from odoo.tests.common import TransactionCase, tagged


@tagged('standard', 'at_install')
class TestProjectStakeholder(TransactionCase):
    """Test Project Stakeholder model functionality."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test data."""
        super().setUpClass()
        
        # Create test project
        cls.project = cls.env['project.project'].create({
            'name': 'Stakeholder Test Event',
            'partner_id': cls.env['res.partner'].create({
                'name': 'Test Customer',
                'email': 'customer@example.com',
            }).id,
        })
        
        # Create test partners
        cls.client_partner = cls.env['res.partner'].create({
            'name': 'Client Contact',
            'email': 'client@example.com',
        })
        
        cls.vendor_partner = cls.env['res.partner'].create({
            'name': 'Vendor Contact',
            'email': 'vendor@example.com',
            'supplier_rank': 1,
        })
    
    def test_stakeholder_creation(self):
        """Test creating a stakeholder."""
        stakeholder = self.env['project.stakeholder'].create({
            'project_id': self.project.id,
            'partner_id': self.client_partner.id,
            'role': 'Event Coordinator',
            'is_client': True,
        })
        
        self.assertEqual(stakeholder.project_id, self.project)
        self.assertEqual(stakeholder.partner_id, self.client_partner)
        self.assertEqual(stakeholder.role, 'Event Coordinator')
        self.assertTrue(stakeholder.is_client)
        self.assertFalse(stakeholder.is_vendor)
    
    def test_stakeholder_vendor_auto_detection(self):
        """Test vendor flag is auto-set when partner is supplier."""
        stakeholder = self.env['project.stakeholder'].create({
            'project_id': self.project.id,
            'partner_id': self.vendor_partner.id,
        })
        
        # onchange should set is_vendor=True
        stakeholder._onchange_partner_id()
        
        self.assertTrue(stakeholder.is_vendor)
        self.assertFalse(stakeholder.is_client)
    
    def test_stakeholder_contact_info_related(self):
        """Test contact info fields are related correctly."""
        stakeholder = self.env['project.stakeholder'].create({
            'project_id': self.project.id,
            'partner_id': self.client_partner.id,
            'is_client': True,
        })
        
        stakeholder.invalidate_recordset()
        
        self.assertEqual(stakeholder.email, self.client_partner.email)
        self.assertEqual(stakeholder.phone, self.client_partner.phone)
    
    def test_stakeholder_role_auto_set(self):
        """Test role is auto-set based on vendor category."""
        stakeholder = self.env['project.stakeholder'].create({
            'project_id': self.project.id,
            'partner_id': self.vendor_partner.id,
            'is_vendor': True,
            'vendor_category': 'dj',
        })
        
        stakeholder._onchange_vendor_details()
        
        self.assertEqual(stakeholder.role, 'DJ')
    
    def test_stakeholder_count_computation(self):
        """Test stakeholder counts on project."""
        # Create client stakeholders
        self.env['project.stakeholder'].create({
            'project_id': self.project.id,
            'partner_id': self.client_partner.id,
            'is_client': True,
            'role': 'Bride',
        })
        
        # Create vendor stakeholder
        self.env['project.stakeholder'].create({
            'project_id': self.project.id,
            'partner_id': self.vendor_partner.id,
            'is_vendor': True,
            'role': 'DJ',
        })
        
        self.project.invalidate_recordset()
        
        self.assertEqual(self.project.client_count, 1)
        self.assertEqual(self.project.vendor_count, 1)
    
    def test_stakeholder_cascade_delete(self):
        """Test stakeholders are deleted when project is deleted."""
        stakeholder = self.env['project.stakeholder'].create({
            'project_id': self.project.id,
            'partner_id': self.client_partner.id,
            'is_client': True,
        })
        
        stakeholder_id = stakeholder.id
        
        # Delete project
        self.project.unlink()
        
        # Stakeholder should be deleted
        self.assertFalse(self.env['project.stakeholder'].browse(stakeholder_id).exists())
    
    def test_stakeholder_action_open_partner(self):
        """Test action to open partner form."""
        stakeholder = self.env['project.stakeholder'].create({
            'project_id': self.project.id,
            'partner_id': self.client_partner.id,
            'is_client': True,
        })
        
        action = stakeholder.action_open_partner()
        
        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['res_model'], 'res.partner')
        self.assertEqual(action['res_id'], self.client_partner.id)
