# -*- coding: utf-8 -*-
"""
Migration: Map legacy PTT vendor/client flags to native Odoo ranks.

This keeps vendor/client identification aligned with Odoo best practice:
- supplier_rank > 0 indicates a vendor
- customer_rank > 0 indicates a customer
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Pre-migration: Copy ptt_is_vendor/ptt_is_client to native ranks."""
    if not version:
        return

    _logger.info("PTT Business Core: Starting pre-migration 19.0.4.2.2")

    # Map ptt_is_vendor -> supplier_rank
    cr.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'res_partner' AND column_name = 'ptt_is_vendor'
    """)
    if cr.fetchone():
        cr.execute("""
            UPDATE res_partner
            SET supplier_rank = 1
            WHERE ptt_is_vendor = True AND (supplier_rank IS NULL OR supplier_rank = 0)
        """)
        _logger.info("Mapped %s partners to supplier_rank", cr.rowcount)
    else:
        _logger.info("ptt_is_vendor column not found, skipping supplier_rank mapping")

    # Map ptt_is_client -> customer_rank
    cr.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'res_partner' AND column_name = 'ptt_is_client'
    """)
    if cr.fetchone():
        cr.execute("""
            UPDATE res_partner
            SET customer_rank = 1
            WHERE ptt_is_client = True AND (customer_rank IS NULL OR customer_rank = 0)
        """)
        _logger.info("Mapped %s partners to customer_rank", cr.rowcount)
    else:
        _logger.info("ptt_is_client column not found, skipping customer_rank mapping")

    _logger.info("PTT Business Core: Pre-migration 19.0.4.2.2 complete")
