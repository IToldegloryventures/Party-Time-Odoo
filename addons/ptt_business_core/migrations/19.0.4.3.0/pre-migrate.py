"""
Migration 19.0.4.3.0 - Clean up fake AI-generated products

This migration removes products that were incorrectly added and do not exist
in the official QuickBooks product list (ProductsServicesList_Party_Time_Texas_1_7_2026.csv).

Products being DELETED:
- All 20 DJ Add-on products (DJ-ADDON-*)
- Duplicate/incorrect product variants
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Remove fake products that don't exist in QuickBooks."""
    if not version:
        return

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

    # Build the SQL IN clause
    codes_str = "', '".join(fake_addon_codes)

    # First, find all product.product (variants) for these templates
    cr.execute(f"""
        SELECT pp.id
        FROM product_product pp
        JOIN product_template pt ON pp.product_tmpl_id = pt.id
        WHERE pt.default_code IN ('{codes_str}')
    """)
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
    cr.execute(f"""
        DELETE FROM product_template
        WHERE default_code IN ('{codes_str}')
    """)
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
