# -*- coding: utf-8 -*-
"""Migration script to populate ptt_vendor_status field for existing vendors.

This migration sets the ptt_vendor_status field based on existing data:
- Vendors with active=True get status 'active'
- Vendors with ptt_pending_review=True get status 'pending_review'
- Vendors with active=False (and not pending) get status 'inactive'
- New vendors (no prior data) get status 'new'
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return

    _logger.info(
        "PTT Vendor Management: Migrating to ptt_vendor_status field"
    )

    # First, check if ptt_pending_review column exists (it was a stored boolean before)
    cr.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'res_partner' 
        AND column_name = 'ptt_pending_review'
    """)
    has_pending_review = cr.fetchone()

    # Set status based on existing data for vendors (supplier_rank > 0)
    if has_pending_review:
        # If ptt_pending_review was a stored field, use it
        cr.execute("""
            UPDATE res_partner
            SET ptt_vendor_status = CASE
                WHEN ptt_pending_review = TRUE THEN 'pending_review'
                WHEN active = TRUE THEN 'active'
                ELSE 'inactive'
            END
            WHERE supplier_rank > 0
            AND ptt_vendor_status IS NULL
        """)
    else:
        # Otherwise, just use active status
        cr.execute("""
            UPDATE res_partner
            SET ptt_vendor_status = CASE
                WHEN active = TRUE THEN 'active'
                ELSE 'inactive'
            END
            WHERE supplier_rank > 0
            AND ptt_vendor_status IS NULL
        """)

    updated_count = cr.rowcount
    _logger.info(
        "PTT Vendor Management: Set ptt_vendor_status for %d existing vendors",
        updated_count
    )
