# -*- coding: utf-8 -*-
"""HttpCase tests for Vendor Portal controllers."""

from datetime import timedelta
from odoo import fields
from odoo.tests.common import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestVendorPortal(HttpCase):
    """Test Vendor Portal HTTP routes and functionality."""
    
    def setUp(self):
        """Set up test data."""
        super().setUp()
        
        # Create test vendor
        self.vendor = self.env['res.partner'].create({
            'name': 'Portal Test Vendor',
            'email': 'portal_vendor@example.com',
            'supplier_rank': 1,
            'is_company': True,
        })
        
        # Create portal user for vendor
        self.vendor_user = self.env['res.users'].create({
            'name': 'Vendor Portal User',
            'login': 'vendor_portal_user',
            'email': 'vendor_portal@example.com',
            'groups_id': [(6, 0, [self.env.ref('base.group_portal').id])],
        })
        self.vendor_user.partner_id = self.vendor
        
        # Create test project
        self.project = self.env['project.project'].create({
            'name': 'Portal Test Event',
            'partner_id': self.env['res.partner'].create({
                'name': 'Test Customer',
                'email': 'customer@example.com',
            }).id,
            'ptt_event_date': fields.Date.today() + timedelta(days=30),
        })
        
        # Create vendor assignment
        self.assignment = self.env['ptt.project.vendor.assignment'].create({
            'project_id': self.project.id,
            'vendor_id': self.vendor.id,
            'service_type': 'dj',
            'estimated_cost': 1000.0,
            'status': 'pending',
        })
    
    def test_portal_work_orders_list(self):
        """Test work orders list page loads for vendor."""
        self.authenticate('vendor_portal_user', 'vendor_portal_user')
        
        url = '/my/work-orders'
        response = self.url_open(url)
        
        self.assertEqual(response.status_code, 200)
    
    def test_portal_work_order_detail(self):
        """Test work order detail page with access token."""
        url = f'/my/work-orders/{self.assignment.id}/{self.assignment.access_token}'
        response = self.url_open(url)
        
        self.assertEqual(response.status_code, 200)
    
    def test_portal_work_order_accept(self):
        """Test vendor accepts work order via JSON endpoint."""
        url = f'/my/work-orders/{self.assignment.id}/accept'
        data = {
            'access_token': self.assignment.access_token,
        }
        
        response = self.opener.post(url, json=data)
        result = response.json()
        
        self.assignment.invalidate_recordset()
        self.assertEqual(result.get('success'), True)
        self.assertEqual(self.assignment.status, 'confirmed')
    
    def test_portal_work_order_decline(self):
        """Test vendor declines work order via JSON endpoint."""
        url = f'/my/work-orders/{self.assignment.id}/decline'
        data = {
            'access_token': self.assignment.access_token,
            'reason': 'Not available on that date',
        }
        
        response = self.opener.post(url, json=data)
        result = response.json()
        
        self.assignment.invalidate_recordset()
        self.assertEqual(result.get('success'), True)
        self.assertEqual(self.assignment.status, 'declined')
    
    def test_portal_vendor_rfqs_list(self):
        """Test vendor RFQs list page."""
        # Create RFQ
        rfq = self.env['ptt.vendor.rfq'].create({
            'name': 'RFQ-PORTAL-001',
            'project_id': self.project.id,
            'vendor_ids': [(6, 0, [self.vendor.id])],
            'state': 'in_progress',
            'closing_date': fields.Date.today() + timedelta(days=7),
        })
        
        self.authenticate('vendor_portal_user', 'vendor_portal_user')
        
        url = '/my/vendor_rfqs'
        response = self.url_open(url)
        
        self.assertEqual(response.status_code, 200)
    
    def test_portal_vendor_application_form(self):
        """Test vendor application form page."""
        self.authenticate('vendor_portal_user', 'vendor_portal_user')
        
        url = '/vendor/apply'
        response = self.url_open(url)
        
        self.assertEqual(response.status_code, 200)
