# -*- coding: utf-8 -*-
"""Pre-migration for service type canonicalization (19.0.3.2.0).

Maps legacy service_type/vendor_category values to the new QuickBooks-aligned
set so existing records stay valid after selection changes.
"""
import logging
from psycopg2 import sql

_logger = logging.getLogger(__name__)

# Legacy -> new service type codes
SERVICE_TYPE_MAPPING = {
    "photovideo": "photography",
    "live_entertainment": "band",
    "decor": "balloon_decor",
    "rentals": "misc_rental",
}

# All valid service type codes after upgrade
ALLOWED_TYPES = {
    "dj",
    "band",
    "musicians",
    "dancers_characters",
    "casino",
    "photography",
    "videography",
    "photobooth",
    "caricature",
    "balloon_face_painters",
    "catering",
    "av_rentals",
    "lighting",
    "balloon_decor",
    "misc_rental",
    "coordination",
    "transportation",
    "staffing",
    "venue_sourcing",
    "insurance",
    "deposit",
    "discount",
    "refund",
    "cancellation",
    "bad_debt",
    "other",
}

TARGET_COLUMNS = [
    ("ptt_crm_service_line", "service_type"),
    ("ptt_crm_vendor_estimate", "service_type"),
    ("ptt_project_vendor_assignment", "service_type"),
    ("project_template", "vendor_category"),
    ("project_stakeholder", "vendor_category"),
    ("project_stakeholder_template", "vendor_category"),
]


def _column_exists(cr, table, column):
    cr.execute(
        """
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_name = %s AND column_name = %s
        )
        """,
        (table, column),
    )
    return cr.fetchone()[0]


def _apply_mapping(cr, table, column):
    table_id = sql.Identifier(table)
    column_id = sql.Identifier(column)
    
    for old_value, new_value in SERVICE_TYPE_MAPPING.items():
        query = sql.SQL("UPDATE {} SET {} = %s WHERE {} = %s").format(
            table_id, column_id, column_id
        )
        cr.execute(query, (new_value, old_value))
        updated = cr.rowcount
        if updated:
            _logger.info("%s.%s: %s -> %s (%s rows)", table, column, old_value, new_value, updated)

    # Normalize any non-allowed values to "other" to keep records valid
    query = sql.SQL("UPDATE {} SET {} = 'other' WHERE {} IS NOT NULL AND {} NOT IN %s").format(
        table_id, column_id, column_id, column_id
    )
    cr.execute(query, (tuple(ALLOWED_TYPES),))
    normalized = cr.rowcount
    if normalized:
        _logger.info("%s.%s: normalized %s rows to 'other'", table, column, normalized)


def migrate(cr, version):
    if not version:
        return

    _logger.info("PTT Business Core: migrating service types to canonical list")

    for table, column in TARGET_COLUMNS:
        if _column_exists(cr, table, column):
            _apply_mapping(cr, table, column)
        else:
            _logger.info("Skipping %s.%s (column not found)", table, column)

    _logger.info("PTT Business Core: service type migration complete")
