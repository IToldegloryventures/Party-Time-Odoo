# -*- coding: utf-8 -*-
"""
Post-migration script for PTT Business Core 19.0.4.5.0

Backfills the computed datetime fields on project.project:
- ptt_setup_start_time
- ptt_event_start_time  
- ptt_event_end_time

These fields are now computed from ptt_event_date + float time fields.
This migration triggers recomputation for all existing projects.
"""

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """
    Post-migration: Backfill datetime fields on existing projects.
    
    The new computed datetime fields need their values populated for
    existing records. Since they're stored computed fields, we trigger
    recomputation by calling the ORM's recompute mechanism.
    """
    if not version:
        return
    
    _logger.info("PTT Business Core 4.5.0: Backfilling project datetime fields...")
    
    # Import environment after CR is available
    from odoo import api, SUPERUSER_ID
    
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Find all projects with event dates that need datetime computation
    projects = env['project.project'].search([
        ('ptt_event_date', '!=', False),
    ])
    
    if not projects:
        _logger.info("No projects with event dates found - nothing to backfill")
        return
    
    _logger.info(f"Found {len(projects)} projects to backfill datetime fields")
    
    # Trigger recomputation of the datetime fields
    # The compute methods will be called automatically
    fields_to_recompute = [
        'ptt_setup_start_time',
        'ptt_event_start_time',
        'ptt_event_end_time',
    ]
    
    for field_name in fields_to_recompute:
        field = projects._fields.get(field_name)
        if field and field.compute:
            _logger.info(f"Recomputing {field_name} for {len(projects)} projects...")
            env.add_to_compute(field, projects)
    
    # Flush the computations to the database
    projects.flush_recordset(fields_to_recompute)
    
    _logger.info("PTT Business Core 4.5.0: Datetime field backfill complete")
