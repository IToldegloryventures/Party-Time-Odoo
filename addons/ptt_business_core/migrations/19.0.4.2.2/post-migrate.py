# -*- coding: utf-8 -*-
"""
Migration: Update Studio field x_plan2_id label to avoid conflict with ptt_event_id.

Both fields exist on project.project with label "Event ID". This causes Odoo warnings.
We rename the deprecated Studio field label to indicate it's legacy.
"""
import json
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Post-migration: Update x_plan2_id field label to avoid duplicate label warning."""
    if not version:
        return

    _logger.info("PTT Business Core: Starting post-migration 19.0.4.2.2")

    # In Odoo 19, field_description is a JSONB column with language translations
    # Format: {"en_US": "Label Text", "fr_FR": "Texte du libellé"}
    # We need to update all language keys to the new label
    new_label = "Event ID (Legacy - Do Not Use)"
    
    # First check if the field exists and get current description
    cr.execute("""
        SELECT id, field_description 
        FROM ir_model_fields
        WHERE model = 'project.project'
        AND name = 'x_plan2_id'
    """)
    result = cr.fetchone()
    
    if result:
        field_id, current_desc = result
        
        # Build new JSON description - update all existing language keys
        if current_desc and isinstance(current_desc, dict):
            new_desc = {lang: new_label for lang in current_desc.keys()}
        else:
            # Default to English if no translations exist
            new_desc = {"en_US": new_label}
        
        cr.execute("""
            UPDATE ir_model_fields
            SET field_description = %s::jsonb
            WHERE id = %s
        """, (json.dumps(new_desc), field_id))
        
        _logger.info(f"Updated x_plan2_id field label to '{new_label}'")
    else:
        _logger.info("x_plan2_id field not found in ir_model_fields, skipping")

    _logger.info("PTT Business Core: Post-migration 19.0.4.2.2 complete")
