# -*- coding: utf-8 -*-
"""
Migration hooks for PTT Business Core module.

This module handles data migration from Studio fields (x_studio_*) to proper
PTT custom fields (ptt_*). The migration is safe to run multiple times and
works for both pre_prod and main (production) deployments.
"""
import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """
    Post-initialization hook to migrate data from x_studio_* fields to ptt_* fields.
    
    This runs after the module is installed/upgraded. It:
    1. Copies data from x_studio_* columns to ptt_* columns (if x_studio_* exists)
    2. Does NOT delete x_studio_* columns (Odoo Studio manages those)
    
    Safe to run multiple times - only copies where ptt_* is empty and x_studio_* has data.
    """
    _logger.info("PTT Business Core: Starting Studio field migration...")
    
    # Migrate CRM Lead fields
    _migrate_crm_lead_fields(env)
    
    # Migrate Project fields
    _migrate_project_fields(env)
    
    _logger.info("PTT Business Core: Studio field migration complete.")


def _migrate_crm_lead_fields(env):
    """Migrate x_studio_* fields to ptt_* fields on crm.lead."""
    cr = env.cr
    
    # Check if x_studio columns exist
    cr.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'crm_lead' 
        AND column_name IN ('x_studio_event_name', 'x_studio_event_date', 
                           'x_studio_venue_name', 'x_studio_venue_address')
    """)
    existing_cols = [row[0] for row in cr.fetchall()]
    
    if not existing_cols:
        _logger.info("PTT Business Core: No x_studio_* columns found on crm.lead - skipping CRM migration")
        return
    
    _logger.info(f"PTT Business Core: Found Studio columns on crm.lead: {existing_cols}")
    
    # Migrate each field (only where ptt_* is NULL and x_studio_* has data)
    migrations = [
        ('x_studio_event_name', 'ptt_event_name'),
        ('x_studio_event_date', 'ptt_event_date'),
        ('x_studio_venue_name', 'ptt_venue_name'),
        ('x_studio_venue_address', 'ptt_venue_address'),
    ]
    
    for studio_col, ptt_col in migrations:
        if studio_col in existing_cols:
            # Check if ptt column exists
            cr.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'crm_lead' AND column_name = %s
            """, (ptt_col,))
            
            if cr.fetchone():
                cr.execute(f"""
                    UPDATE crm_lead 
                    SET {ptt_col} = {studio_col}
                    WHERE {ptt_col} IS NULL 
                    AND {studio_col} IS NOT NULL
                """)
                count = cr.rowcount
                if count > 0:
                    _logger.info(f"PTT Business Core: Migrated {count} records from {studio_col} to {ptt_col}")
            else:
                _logger.warning(f"PTT Business Core: Column {ptt_col} does not exist yet on crm.lead - will migrate on next upgrade")


def _migrate_project_fields(env):
    """Migrate x_studio_* fields to ptt_* fields on project.project."""
    cr = env.cr
    
    # Check if x_studio columns exist on project
    cr.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'project_project' 
        AND column_name IN ('x_studio_event_name', 'x_studio_event_date', 
                           'x_studio_venue_name', 'x_studio_venue_address')
    """)
    existing_cols = [row[0] for row in cr.fetchall()]
    
    if not existing_cols:
        _logger.info("PTT Business Core: No x_studio_* columns found on project.project - skipping Project migration")
        return
    
    _logger.info(f"PTT Business Core: Found Studio columns on project.project: {existing_cols}")
    
    # Migrate each field
    migrations = [
        ('x_studio_event_name', 'ptt_event_name'),
        ('x_studio_event_date', 'ptt_event_date'),
        ('x_studio_venue_name', 'ptt_venue_name'),
        ('x_studio_venue_address', 'ptt_venue_address'),
    ]
    
    for studio_col, ptt_col in migrations:
        if studio_col in existing_cols:
            cr.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'project_project' AND column_name = %s
            """, (ptt_col,))
            
            if cr.fetchone():
                cr.execute(f"""
                    UPDATE project_project 
                    SET {ptt_col} = {studio_col}
                    WHERE {ptt_col} IS NULL 
                    AND {studio_col} IS NOT NULL
                """)
                count = cr.rowcount
                if count > 0:
                    _logger.info(f"PTT Business Core: Migrated {count} project records from {studio_col} to {ptt_col}")
