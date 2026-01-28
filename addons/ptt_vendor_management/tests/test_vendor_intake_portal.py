# -*- coding: utf-8 -*-
"""HttpCase tests for Vendor Intake Portal (public application form)."""

from odoo.tests.common import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestVendorIntakePortal(HttpCase):
    """Test public Vendor Intake Portal form."""
    
    def test_vendor_intake_form_public_access(self):
        """Test public vendor intake form is accessible."""
        url = '/vendor/intake'
        response = self.url_open(url)
        
        self.assertEqual(response.status_code, 200)
        # Form should be accessible without authentication
    
    def test_vendor_intake_form_submission(self):
        """Test vendor intake form submission creates partner."""
        url = '/vendor/intake/submit'
        
        # Count partners before
        partner_count_before = self.env['res.partner'].search_count([
            ('email', '=', 'new_vendor@example.com')
        ])
        
        # Submit form (using form data format)
        data = {
            'company_name': 'New Vendor Company',
            'email': 'new_vendor@example.com',
            'phone': '555-1234',
            'address': '123 Test St',
            'vendor_type': 'dj',
        }
        
        # Use url_open with data parameter for POST
        response = self.url_open(url, data=data)
        
        # Check partner was created
        partner_count_after = self.env['res.partner'].search_count([
            ('email', '=', 'new_vendor@example.com')
        ])
        
        self.assertEqual(partner_count_after, partner_count_before + 1)
        
        # Verify partner details
        partner = self.env['res.partner'].search([
            ('email', '=', 'new_vendor@example.com')
        ], limit=1)
        
        self.assertEqual(partner.name, 'New Vendor Company')
        self.assertEqual(partner.supplier_rank, 1)
        self.assertEqual(partner.street, '123 Test St')
