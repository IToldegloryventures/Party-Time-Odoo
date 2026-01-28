# -*- coding: utf-8 -*-
"""
Migration 19.0.4.3.0 - Clean up fake AI-generated products AND migrate x_studio_* fields

This migration:
1. Removes products that were incorrectly added (DJ-ADDON-*)
2. Migrates data from x_studio_* fields to ptt_* fields on crm.lead
3. Drops duplicate x_studio_* columns to avoid label conflicts
"""
import logging
from psycopg2 import sql

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Remove fake products and migrate x_studio_* fields to ptt_*."""
    if not version:
        return

    _logger.info("PTT Migration 19.0.4.3.0: Starting migration...")

    # =========================================================================
    # STEP 0: Migrate x_studio_* data to ptt_* columns on crm_lead
    # This prevents "Two fields have the same label" errors
    # =========================================================================
    _logger.info("Migrating x_studio_* fields to ptt_* fields on crm_lead...")
    
    # Map of x_studio_* column to ptt_* column (simple same-type fields)
    field_mappings = [
        ('x_studio_event_name', 'ptt_event_name'),
        ('x_studio_event_date', 'ptt_event_date'),
        ('x_studio_event_type', 'ptt_event_type'),
        ('x_studio_venue_name', 'ptt_venue_name'),
        ('x_studio_venue_address', 'ptt_venue_address'),
        ('x_studio_attire', 'ptt_attire'),
    ]
    
    # Time fields need special handling - x_studio is timestamp, ptt is float (hours)
    time_field_mappings = [
        ('x_studio_setup_time', 'ptt_setup_time'),
        ('x_studio_start_time', 'ptt_start_time'),
        ('x_studio_end_time', 'ptt_end_time'),
    ]
    
    for x_studio_col, ptt_col in field_mappings:
        # Check if x_studio column exists
        cr.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'crm_lead' AND column_name = %s
        """, (x_studio_col,))
        
        if cr.fetchone():
            # Check if ptt column exists
            cr.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'crm_lead' AND column_name = %s
            """, (ptt_col,))
            
            if cr.fetchone():
                # Both exist - copy data from x_studio to ptt where ptt is NULL
                query = sql.SQL("UPDATE crm_lead SET {} = {} WHERE {} IS NULL AND {} IS NOT NULL").format(
                    sql.Identifier(ptt_col),
                    sql.Identifier(x_studio_col),
                    sql.Identifier(ptt_col),
                    sql.Identifier(x_studio_col)
                )
                cr.execute(query)
                _logger.info(f"Copied {cr.rowcount} values from {x_studio_col} to {ptt_col}")
            
            # Drop the x_studio column to avoid label conflict
            query = sql.SQL("ALTER TABLE crm_lead DROP COLUMN IF EXISTS {}").format(
                sql.Identifier(x_studio_col)
            )
            cr.execute(query)
            _logger.info(f"Dropped column {x_studio_col}")
    
    # Handle time fields - convert timestamp to float (decimal hours)
    for x_studio_col, ptt_col in time_field_mappings:
        cr.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'crm_lead' AND column_name = %s
        """, (x_studio_col,))
        
        if cr.fetchone():
            cr.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'crm_lead' AND column_name = %s
            """, (ptt_col,))
            
            if cr.fetchone():
                # Convert timestamp to decimal hours (e.g., 14:30 -> 14.5)
                query = sql.SQL("UPDATE crm_lead SET {} = EXTRACT(HOUR FROM {}) + EXTRACT(MINUTE FROM {}) / 60.0 WHERE {} IS NULL AND {} IS NOT NULL").format(
                    sql.Identifier(ptt_col),
                    sql.Identifier(x_studio_col),
                    sql.Identifier(x_studio_col),
                    sql.Identifier(ptt_col),
                    sql.Identifier(x_studio_col)
                )
                cr.execute(query)
                _logger.info(f"Converted {cr.rowcount} timestamp values from {x_studio_col} to float hours in {ptt_col}")
            
            # Drop the x_studio column
            query = sql.SQL("ALTER TABLE crm_lead DROP COLUMN IF EXISTS {}").format(
                sql.Identifier(x_studio_col)
            )
            cr.execute(query)
            _logger.info(f"Dropped column {x_studio_col}")
    
    # =========================================================================
    # STEP 0.5: Drop orphaned x_studio_* columns that still cause label conflicts
    # These are leftover Studio fields that weren't mapped above
    # =========================================================================
    orphaned_columns = [
        'x_studio_end_time_1',  # Duplicate of ptt_end_time
        'x_studio_boolean_field_297_1jckjk5dc',  # Duplicate "New CheckBox"
        'x_studio_boolean_field_1vp_1jckie6sq',  # Duplicate "New CheckBox"
    ]
    for col in orphaned_columns:
        query = sql.SQL("ALTER TABLE crm_lead DROP COLUMN IF EXISTS {}").format(
            sql.Identifier(col)
        )
        cr.execute(query)
        _logger.info(f"Dropped orphaned column {col}")
    
    # Also clean up ir.model.fields entries for x_studio_* fields on crm.lead
    cr.execute("""
        DELETE FROM ir_model_fields 
        WHERE model = 'crm.lead' 
        AND name LIKE 'x_studio_%'
    """)
    _logger.info(f"Cleaned up {cr.rowcount} ir.model.fields entries for x_studio_* fields")
    
    _logger.info("PTT Migration 19.0.4.3.0: Cleaning up fake AI-generated products...")

    # =========================================================================
    # STEP 1: Delete all fake DJ Add-on products by default_code pattern
    # These were AI-generated and don't exist in QuickBooks
    # =========================================================================
    fake_addon_codes = [
        'DJ-ADDON-HOUR',
        'DJ-ADDON-LIGHT',
        'DJ-ADDON-MC',
        'DJ-ADDON-ASSIST',
        'DJ-ADDON-QUEUE',
        'DJ-ADDON-UPLIGHT',
        'DJ-ADDON-VIDEO',
        'DJ-ADDON-COHOST',
        'DJ-ADDON-BRAND',
        'DJ-ADDON-RAFFLE',
        'DJ-ADDON-MIC',
        'DJ-ADDON-FACADE',
        'DJ-ADDON-VOICE',
        'DJ-ADDON-REMIX',
        'DJ-ADDON-SPONSOR',
        'DJ-ADDON-CUES',
        'DJ-ADDON-PLAYLIST',
        'DJ-ADDON-TIMELINE',
        'DJ-ADDON-TRANS',
        'DJ-ADDON-APP',
    ]

    # First, find all product.product (variants) for these templates
    placeholders = ','.join(['%s'] * len(fake_addon_codes))
    query = f"""
        SELECT pp.id
        FROM product_product pp
        JOIN product_template pt ON pp.product_tmpl_id = pt.id
        WHERE pt.default_code IN ({placeholders})
    """
    cr.execute(query, tuple(fake_addon_codes))
    variant_ids = [row[0] for row in cr.fetchall()]

    if variant_ids:
        _logger.info(f"Found {len(variant_ids)} product variants to delete")

        # Delete from sale_order_line first (FK constraint)
        cr.execute("""
            DELETE FROM sale_order_line
            WHERE product_id IN %s
        """, (tuple(variant_ids),))
        deleted_sol = cr.rowcount
        _logger.info(f"Deleted {deleted_sol} sale order lines referencing fake products")

        # Delete from purchase_order_line (FK constraint)
        cr.execute("""
            DELETE FROM purchase_order_line
            WHERE product_id IN %s
        """, (tuple(variant_ids),))
        deleted_pol = cr.rowcount
        _logger.info(f"Deleted {deleted_pol} purchase order lines referencing fake products")

        # Delete product variants
        cr.execute("""
            DELETE FROM product_product
            WHERE id IN %s
        """, (tuple(variant_ids),))
        _logger.info(f"Deleted {cr.rowcount} product variants")

    # Now delete the product templates
    placeholders = ','.join(['%s'] * len(fake_addon_codes))
    query = f"""
        DELETE FROM product_template
        WHERE default_code IN ({placeholders})
    """
    cr.execute(query, tuple(fake_addon_codes))
    deleted_templates = cr.rowcount
    _logger.info(f"Deleted {deleted_templates} fake product templates")

    # =========================================================================
    # STEP 2: Clean up ir.model.data references to deleted products
    # =========================================================================
    cr.execute("""
        DELETE FROM ir_model_data
        WHERE module = 'ptt_business_core'
        AND model = 'product.template'
        AND name LIKE 'product_template_dj_addon_%'
    """)
    _logger.info(f"Cleaned up {cr.rowcount} ir.model.data references")

    _logger.info("PTT Migration 19.0.4.3.0: Fake product cleanup complete!")
