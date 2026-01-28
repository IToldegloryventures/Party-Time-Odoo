# -*- coding: utf-8 -*-
"""
Pre-migration script for ptt_vendor_management 19.0.2.0.0

This migration:
1. Migrates x_is_vendor data to supplier_rank (native Odoo vendor flag)
2. Renames all x_vendor_* fields to ptt_vendor_* following Odoo best practices
"""
import logging
from psycopg2 import sql

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """
    Pre-migration: Transfer x_is_vendor data to supplier_rank and rename fields.
    """
    if not version:
        return
    
    _logger.info("PTT Vendor Management: Starting pre-migration 19.0.2.0.0")
    
    # === PHASE 1: Migrate x_is_vendor to supplier_rank ===
    
    # Check if x_is_vendor column exists
    cr.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'res_partner' AND column_name = 'x_is_vendor'
    """)
    
    if cr.fetchone():
        # Transfer x_is_vendor data to supplier_rank
        cr.execute("""
            UPDATE res_partner
            SET supplier_rank = 1
            WHERE x_is_vendor = True AND (supplier_rank IS NULL OR supplier_rank = 0)
        """)
        updated_count = cr.rowcount
        _logger.info(f"PTT Vendor Management: Migrated {updated_count} vendors to supplier_rank")
        
        # Remove the x_is_vendor column from the database
        cr.execute("ALTER TABLE res_partner DROP COLUMN IF EXISTS x_is_vendor")
        _logger.info("PTT Vendor Management: Dropped x_is_vendor column")
        
        # Remove the field definition from ir_model_fields
        cr.execute("""
            DELETE FROM ir_model_fields 
            WHERE name = 'x_is_vendor' AND model = 'res.partner'
        """)
    
    # === PHASE 2: Rename x_vendor_* fields to ptt_vendor_* ===
    
    # Field renames for res.partner table
    field_renames = [
        ('x_vendor_tier', 'ptt_vendor_tier'),
        ('x_vendor_contact_role', 'ptt_vendor_contact_role'),
        ('x_vendor_document_ids', 'ptt_vendor_document_ids'),
        ('x_vendor_document_count', 'ptt_vendor_document_count'),
        ('x_vendor_compliance_status', 'ptt_vendor_compliance_status'),
        ('x_vendor_notes', 'ptt_vendor_notes'),
        ('x_vendor_rating', 'ptt_vendor_rating'),
    ]
    
    for old_name, new_name in field_renames:
        # Check if old column exists
        cr.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'res_partner' AND column_name = %s
        """, (old_name,))
        
        if cr.fetchone():
            # Check if new column already exists
            cr.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'res_partner' AND column_name = %s
            """, (new_name,))
            
            if not cr.fetchone():
                # Rename the column
                query = sql.SQL("ALTER TABLE res_partner RENAME COLUMN {} TO {}").format(
                    sql.Identifier(old_name),
                    sql.Identifier(new_name)
                )
                cr.execute(query)
                _logger.info(f"PTT Vendor Management: Renamed column {old_name} to {new_name}")
            else:
                # Copy data to new column and drop old
                _logger.info(f"PTT Vendor Management: {new_name} already exists, copying data")
                query = sql.SQL("UPDATE res_partner SET {} = {} WHERE {} IS NOT NULL AND ({} IS NULL OR {} = '')").format(
                    sql.Identifier(new_name),
                    sql.Identifier(old_name),
                    sql.Identifier(old_name),
                    sql.Identifier(new_name),
                    sql.Identifier(new_name)
                )
                cr.execute(query)
                query = sql.SQL("ALTER TABLE res_partner DROP COLUMN IF EXISTS {}").format(
                    sql.Identifier(old_name)
                )
                cr.execute(query)
        
        # Update ir_model_fields
        cr.execute("""
            UPDATE ir_model_fields 
            SET name = %s 
            WHERE name = %s AND model = 'res.partner'
        """, (new_name, old_name))
    
    # Rename the Many2many relation table column if exists
    cr.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'res_partner_vendor_service_tag_rel'
    """)
    # The relation table should keep working as it references partner_id and tag_id
    
    # Clean up ir_model_data references
    cr.execute("""
        DELETE FROM ir_model_data 
        WHERE model = 'ir.model.fields' 
        AND res_id NOT IN (SELECT id FROM ir_model_fields)
    """)
    
    _logger.info("PTT Vendor Management: Pre-migration 19.0.2.0.0 completed successfully")
