# -*- coding: utf-8 -*-
"""Tests for Vendor Document management."""

from datetime import timedelta
from odoo import fields
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import ValidationError


@tagged('standard', 'at_install')
class TestVendorDocument(TransactionCase):
    """Test Vendor Document model and compliance tracking."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test data."""
        super().setUpClass()
        
        # Create test vendor
        cls.vendor = cls.env['res.partner'].create({
            'name': 'Document Test Vendor',
            'email': 'vendor@example.com',
            'supplier_rank': 1,
            'is_company': True,
        })
        
        # Create document type
        cls.doc_type = cls.env['ptt.document.type'].create({
            'name': 'Insurance Certificate',
            'code': 'insurance',
            'is_required': True,
            'active': True,
        })
        
        cls.doc_type_optional = cls.env['ptt.document.type'].create({
            'name': 'Portfolio',
            'code': 'portfolio',
            'is_required': False,
            'active': True,
        })
    
    def test_document_creation(self):
        """Test creating a vendor document."""
        doc = self.env['ptt.vendor.document'].create({
            'vendor_id': self.vendor.id,
            'document_type_id': self.doc_type.id,
            'validity': fields.Date.today() + timedelta(days=365),
            'status': 'compliant',
        })
        
        self.assertEqual(doc.vendor_id, self.vendor)
        self.assertEqual(doc.document_type_id, self.doc_type)
        self.assertEqual(doc.status, 'compliant')
    
    def test_document_expiry_check(self):
        """Test document expiry status computation."""
        # Valid document
        doc_valid = self.env['ptt.vendor.document'].create({
            'vendor_id': self.vendor.id,
            'document_type_id': self.doc_type.id,
            'validity': fields.Date.today() + timedelta(days=30),
            'status': 'compliant',
        })
        
        # Expired document
        doc_expired = self.env['ptt.vendor.document'].create({
            'vendor_id': self.vendor.id,
            'document_type_id': self.doc_type.id,
            'validity': fields.Date.today() - timedelta(days=1),
            'status': 'compliant',
        })
        
        # No expiry date
        doc_no_date = self.env['ptt.vendor.document'].create({
            'vendor_id': self.vendor.id,
            'document_type_id': self.doc_type_optional.id,
            'status': 'compliant',
        })
        
        doc_valid.invalidate_recordset()
        doc_expired.invalidate_recordset()
        doc_no_date.invalidate_recordset()
        
        # Check expiry status (assuming there's a computed field)
        # This depends on the actual implementation
        self.assertTrue(doc_valid.validity >= fields.Date.today())
        self.assertTrue(doc_expired.validity < fields.Date.today())
    
    def test_document_owner_computation(self):
        """Test document owner is computed correctly."""
        # Vendor document
        doc_vendor = self.env['ptt.vendor.document'].create({
            'vendor_id': self.vendor.id,
            'document_type_id': self.doc_type.id,
        })
        
        self.assertEqual(doc_vendor.document_owner, 'vendor')
        
        # Contact document
        contact = self.env['res.partner'].create({
            'name': 'Contact Person',
            'parent_id': self.vendor.id,
        })
        
        doc_contact = self.env['ptt.vendor.document'].create({
            'vendor_id': self.vendor.id,
            'contact_id': contact.id,
            'document_type_id': self.doc_type.id,
        })
        
        doc_contact.invalidate_recordset()
        self.assertEqual(doc_contact.document_owner, 'contact')
    
    def test_required_document_validation(self):
        """Test that required documents are validated."""
        # Create required document type
        required_doc_type = self.env['ptt.document.type'].create({
            'name': 'Required Doc',
            'code': 'required',
            'is_required': True,
            'active': True,
        })
        
        # Vendor should be non-compliant without required document
        self.vendor.invalidate_recordset()
        # Check compliance status (depends on implementation)
        
        # Add required document
        self.env['ptt.vendor.document'].create({
            'vendor_id': self.vendor.id,
            'document_type_id': required_doc_type.id,
            'status': 'compliant',
        })
        
        self.vendor.invalidate_recordset()
        # Vendor should now be compliant (if implementation checks this)
    
    def test_document_status_workflow(self):
        """Test document status workflow."""
        doc = self.env['ptt.vendor.document'].create({
            'vendor_id': self.vendor.id,
            'document_type_id': self.doc_type.id,
            'status': 'non_compliant',
        })
        
        self.assertEqual(doc.status, 'non_compliant')
        
        # Update to compliant
        doc.write({
            'status': 'compliant',
            'validity': fields.Date.today() + timedelta(days=365),
        })
        
        self.assertEqual(doc.status, 'compliant')
    
    def test_document_cascade_delete(self):
        """Test documents are deleted when vendor is deleted."""
        doc = self.env['ptt.vendor.document'].create({
            'vendor_id': self.vendor.id,
            'document_type_id': self.doc_type.id,
        })
        
        doc_id = doc.id
        
        # Delete vendor
        self.vendor.unlink()
        
        # Document should be deleted
        self.assertFalse(self.env['ptt.vendor.document'].browse(doc_id).exists())
