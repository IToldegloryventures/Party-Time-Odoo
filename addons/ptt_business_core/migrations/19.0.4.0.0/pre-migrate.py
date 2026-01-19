# -*- coding: utf-8 -*-
"""
Migration: Copy x_plan2_id data to new ptt_event_id field.

The x_plan2_id field is reserved by Odoo's analytic module and has a foreign key
constraint. We create a new ptt_event_id field for PTT event tracking and migrate
existing data.
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Pre-migration: Copy x_plan2_id values to ptt_event_id before column is created."""
    if not version:
        return

    _logger.info("PTT Business Core: Starting migration to 19.0.4.0.0")

    # Check if x_plan2_id column exists and has data
    cr.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'project_project' 
        AND column_name = 'x_plan2_id'
    """)
    
    if cr.fetchone():
        # Check if ptt_event_id column already exists
        cr.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'project_project' 
            AND column_name = 'ptt_event_id'
        """)
        
        if not cr.fetchone():
            # Create the new column first
            _logger.info("Creating ptt_event_id column on project_project")
            cr.execute("""
                ALTER TABLE project_project 
                ADD COLUMN IF NOT EXISTS ptt_event_id VARCHAR
            """)
            
            # Copy data from x_plan2_id to ptt_event_id
            # Note: x_plan2_id might be integer FK, so we cast to varchar
            _logger.info("Copying x_plan2_id data to ptt_event_id")
            cr.execute("""
                UPDATE project_project 
                SET ptt_event_id = x_plan2_id::VARCHAR
                WHERE x_plan2_id IS NOT NULL
                AND ptt_event_id IS NULL
            """)
            
            count = cr.rowcount
            _logger.info(f"Migrated {count} event IDs from x_plan2_id to ptt_event_id")
        else:
            _logger.info("ptt_event_id column already exists, skipping creation")
    else:
        _logger.info("x_plan2_id column does not exist, skipping data migration")

    _logger.info("PTT Business Core: Migration to 19.0.4.0.0 complete")
