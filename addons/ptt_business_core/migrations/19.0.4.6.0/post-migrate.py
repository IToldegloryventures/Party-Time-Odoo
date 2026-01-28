# -*- coding: utf-8 -*-
"""
Post-migration: Populate service_type_id from service_type Selection values.

This migration maps existing ptt.crm.service.line records' service_type
Selection values to the new service_type_id Many2one field, linking them
to ptt.vendor.service.type records by matching the 'code' field.

The vendor_service_types.xml data file must be loaded before this runs.
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Populate service_type_id based on service_type code matching."""
    if not version:
        return

    _logger.info(
        "PTT Business Core: Migrating service_type Selection to service_type_id Many2one"
    )

    # Map existing service_type Selection values to service_type_id
    # by matching ptt_vendor_service_type.code
    cr.execute("""
        UPDATE ptt_crm_service_line sl
        SET service_type_id = vst.id
        FROM ptt_vendor_service_type vst
        WHERE sl.service_type = vst.code
          AND sl.service_type_id IS NULL
          AND sl.service_type IS NOT NULL
    """)
    
    updated_count = cr.rowcount
    _logger.info(
        "PTT Business Core: Updated %d service lines with service_type_id",
        updated_count
    )

    # Log any service lines that couldn't be mapped
    cr.execute("""
        SELECT id, service_type
        FROM ptt_crm_service_line
        WHERE service_type_id IS NULL
          AND service_type IS NOT NULL
    """)
    
    unmapped = cr.fetchall()
    if unmapped:
        _logger.warning(
            "PTT Business Core: %d service lines have unmapped service_type values: %s",
            len(unmapped),
            [row[1] for row in unmapped[:10]]  # Show first 10
        )
