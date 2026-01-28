# -*- coding: utf-8 -*-
"""
Migration 19.0.4.4.4 - Drop deprecated event timing columns from project.project.

This migration removes the old `ptt_event_time` and `ptt_event_duration`
columns that were marked as deprecated and builds on the replacement fields
(`ptt_event_start_time` / `ptt_total_hours`). The corresponding
`ir.model.fields` / `ir.model.data` entries are also purged to keep the
metadata clean.
"""
import logging

_logger = logging.getLogger(__name__)
DEPRECATED_COLUMNS = ["ptt_event_time", "ptt_event_duration"]


def migrate(cr, version):
    """Drop the deprecated fields from Postgres metadata."""
    if not version:
        return

    _logger.info("PTT Migration 19.0.4.4.4: removing deprecated event timing columns")

    for column_name in DEPRECATED_COLUMNS:
        cr.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'project_project'
            AND column_name = %s
        """,
            (column_name,),
        )
        if not cr.fetchone():
            _logger.info("Column %s already absent, skipping", column_name)
            continue

        cr.execute(f"SELECT COUNT(*) FROM project_project WHERE {column_name} IS NOT NULL")
        row = cr.fetchone()
        populated = row[0] if row else 0
        if populated:
            _logger.info(
                "Column %s still has %s rows populated; data will be removed",
                column_name,
                populated,
            )

        cr.execute(f"ALTER TABLE project_project DROP COLUMN IF EXISTS {column_name}")
        _logger.info("Dropped column %s from project.project", column_name)

    columns_tuple = tuple(DEPRECATED_COLUMNS)

    cr.execute(
        """
        DELETE FROM ir_model_fields
        WHERE model = 'project.project'
        AND name IN %s
    """,
        (columns_tuple,),
    )
    _logger.info("Cleared %s entries from ir.model.fields", ", ".join(DEPRECATED_COLUMNS))

    cr.execute(
        """
        DELETE FROM ir_model_data
        WHERE module = 'ptt_business_core'
        AND model = 'ir.model.fields'
        AND name IN %s
    """,
        (columns_tuple,),
    )
    _logger.info("Cleared %s entries from ir.model.data", ", ".join(DEPRECATED_COLUMNS))
