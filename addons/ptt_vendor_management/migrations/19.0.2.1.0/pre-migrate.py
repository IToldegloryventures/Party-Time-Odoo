# -*- coding: utf-8 -*-
"""
Pre-migration script for PTT Vendor Management 19.0.2.1.0

Updates vendor document status values from old computed values to new manual values:
- valid -> compliant
- expired -> non_compliant
- not_applicable -> non_compliant

Also populates document lines for existing vendors that don't have them.
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Migrate status values to new selection options."""
    if not version:
        return
    
    _logger.info("PTT Vendor Management 19.0.2.1.0: Updating document status values...")

    cr.execute("""
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'ptt_vendor_document'
          AND column_name = 'status'
    """)
    if not cr.fetchone():
        _logger.info("  Skipping status migration: ptt_vendor_document.status not found")
        return
    
    # Update status values
    cr.execute("""
        UPDATE ptt_vendor_document 
        SET status = 'compliant' 
        WHERE status = 'valid'
    """)
    compliant_count = cr.rowcount
    _logger.info("  Updated %d documents: valid -> compliant", compliant_count)
    
    cr.execute("""
        UPDATE ptt_vendor_document 
        SET status = 'non_compliant' 
        WHERE status IN ('expired', 'not_applicable') OR status IS NULL
    """)
    non_compliant_count = cr.rowcount
    _logger.info("  Updated %d documents: expired/not_applicable/null -> non_compliant", non_compliant_count)
    
    _logger.info("PTT Vendor Management 19.0.2.1.0: Migration complete")
