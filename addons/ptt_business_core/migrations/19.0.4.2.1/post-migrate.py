# -*- coding: utf-8 -*-
"""
Migration: Update Studio field x_plan2_id label to avoid conflict with ptt_event_id.

Both fields exist on project.project with label "Event ID". This causes Odoo warnings.
We rename the deprecated Studio field label to indicate it's legacy.
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Post-migration: Update x_plan2_id field label to avoid duplicate label warning."""
    if not version:
        return

    _logger.info("PTT Business Core: Starting post-migration 19.0.4.2.1")

    # Update the ir.model.fields record for x_plan2_id to have a different label
    # This prevents the "Two fields have the same label" warning
    cr.execute("""
        UPDATE ir_model_fields
        SET field_description = 'Event ID (Legacy - Do Not Use)'
        WHERE model = 'project.project'
        AND name = 'x_plan2_id'
    """)
    
    updated = cr.rowcount
    if updated:
        _logger.info(f"Updated x_plan2_id field label to 'Event ID (Legacy - Do Not Use)'")
    else:
        _logger.info("x_plan2_id field not found in ir_model_fields, skipping")

    _logger.info("PTT Business Core: Post-migration 19.0.4.2.1 complete")
