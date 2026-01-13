"""
Pre-migration script for ptt_business_core 19.0.3.0.0

This migration renames all x_* fields to ptt_* fields on:
- crm.lead model
- project.project model  
- ptt.project.vendor.assignment model

Following Odoo best practices (x_ prefix reserved for Studio fields).

Reference: https://www.odoo.com/documentation/19.0/developer/reference/backend/orm.html
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """
    Pre-migration: Rename x_* columns to ptt_* on crm_lead table.
    """
    if not version:
        return
    
    _logger.info("PTT Business Core: Starting pre-migration 19.0.3.0.0 - Renaming CRM lead fields")
    
    # Field renames for crm_lead table (x_* to ptt_*)
    crm_lead_renames = [
        # Contact fields
        ('x_date_of_call', 'ptt_date_of_call'),
        ('x_preferred_contact_method', 'ptt_preferred_contact_method'),
        ('x_second_poc_name', 'ptt_second_poc_name'),
        ('x_second_poc_phone', 'ptt_second_poc_phone'),
        ('x_second_poc_email', 'ptt_second_poc_email'),
        # Event identification
        ('x_event_id', 'ptt_event_id'),
        ('x_referral_source', 'ptt_referral_source'),
        # Event overview
        ('x_event_type', 'ptt_event_type'),
        ('x_event_specific_goal', 'ptt_event_specific_goal'),
        ('x_event_date', 'ptt_event_date'),
        ('x_event_time', 'ptt_event_time'),
        ('x_total_hours', 'ptt_total_hours'),
        ('x_estimated_guest_count', 'ptt_estimated_guest_count'),
        ('x_venue_booked', 'ptt_venue_booked'),
        ('x_venue_name', 'ptt_venue_name'),
        ('x_event_location_type', 'ptt_event_location_type'),
        # Services
        ('x_service_dj', 'ptt_service_dj'),
        ('x_service_photovideo', 'ptt_service_photovideo'),
        ('x_service_live_entertainment', 'ptt_service_live_entertainment'),
        ('x_service_lighting', 'ptt_service_lighting'),
        ('x_service_decor', 'ptt_service_decor'),
        ('x_service_venue_sourcing', 'ptt_service_venue_sourcing'),
        ('x_service_catering', 'ptt_service_catering'),
        ('x_service_transportation', 'ptt_service_transportation'),
        ('x_service_rentals', 'ptt_service_rentals'),
        ('x_service_photobooth', 'ptt_service_photobooth'),
        ('x_service_caricature', 'ptt_service_caricature'),
        ('x_service_casino', 'ptt_service_casino'),
        ('x_service_staffing', 'ptt_service_staffing'),
        # CFO contact
        ('x_cfo_name', 'ptt_cfo_name'),
        ('x_cfo_phone', 'ptt_cfo_phone'),
        ('x_cfo_email', 'ptt_cfo_email'),
        ('x_cfo_contact_method', 'ptt_cfo_contact_method'),
        # Relational fields (One2many inverse fields stored on related model, not here)
        # These are just virtual fields, actual columns don't exist on crm_lead
        # ('x_service_line_ids', 'ptt_service_line_ids'),  # One2many - no column
        # ('x_vendor_assignment_ids', 'ptt_vendor_assignment_ids'),  # One2many - no column
    ]
    
    # Rename columns in crm_lead table
    for old_name, new_name in crm_lead_renames:
        _rename_column(cr, 'crm_lead', old_name, new_name)
        _update_ir_model_fields(cr, 'crm.lead', old_name, new_name)
    
    # Update One2many field names in ir_model_fields (no column rename needed)
    one2many_renames = [
        ('x_service_line_ids', 'ptt_service_line_ids'),
        ('x_vendor_assignment_ids', 'ptt_vendor_assignment_ids'),
    ]
    for old_name, new_name in one2many_renames:
        _update_ir_model_fields(cr, 'crm.lead', old_name, new_name)
    
    # === PHASE 2: project.project field renames ===
    _logger.info("PTT Business Core: Renaming project.project fields")
    
    project_renames = [
        ('x_event_id', 'ptt_event_id'),
        ('x_event_type', 'ptt_event_type'),
        ('x_event_date', 'ptt_event_date'),
        ('x_event_time', 'ptt_event_time'),
        ('x_guest_count', 'ptt_guest_count'),
        ('x_venue_name', 'ptt_venue_name'),
        ('x_setup_start_time', 'ptt_setup_start_time'),
        ('x_event_start_time', 'ptt_event_start_time'),
        ('x_event_end_time', 'ptt_event_end_time'),
        ('x_total_hours', 'ptt_total_hours'),
        ('x_teardown_deadline', 'ptt_teardown_deadline'),
        ('x_theme_dress_code', 'ptt_theme_dress_code'),
        ('x_special_requirements_desc', 'ptt_special_requirements_desc'),
        ('x_inclement_weather_plan', 'ptt_inclement_weather_plan'),
        ('x_parking_restrictions_desc', 'ptt_parking_restrictions_desc'),
    ]
    
    for old_name, new_name in project_renames:
        _rename_column(cr, 'project_project', old_name, new_name)
        _update_ir_model_fields(cr, 'project.project', old_name, new_name)
    
    # One2many field rename for project.project
    _update_ir_model_fields(cr, 'project.project', 'x_vendor_assignment_ids', 'ptt_vendor_assignment_ids')
    
    # === PHASE 3: ptt.project.vendor.assignment field renames ===
    _logger.info("PTT Business Core: Renaming ptt.project.vendor.assignment fields")
    
    vendor_assignment_renames = [
        ('x_status', 'ptt_status'),
        ('x_confirmed_date', 'ptt_confirmed_date'),
        ('x_contact_person', 'ptt_contact_person'),
        ('x_contact_phone', 'ptt_contact_phone'),
        ('x_arrival_time', 'ptt_arrival_time'),
        ('x_equipment_notes', 'ptt_equipment_notes'),
    ]
    
    for old_name, new_name in vendor_assignment_renames:
        _rename_column(cr, 'ptt_project_vendor_assignment', old_name, new_name)
        _update_ir_model_fields(cr, 'ptt.project.vendor.assignment', old_name, new_name)
    
    # Clean up orphaned ir_model_data references
    cr.execute("""
        DELETE FROM ir_model_data 
        WHERE model = 'ir.model.fields' 
        AND res_id NOT IN (SELECT id FROM ir_model_fields)
    """)
    
    _logger.info("PTT Business Core: Pre-migration 19.0.3.0.0 completed successfully")


def _rename_column(cr, table, old_name, new_name):
    """Rename a column if it exists and new column doesn't exist."""
    # Check if old column exists
    cr.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = %s AND column_name = %s
    """, (table, old_name))
    
    if not cr.fetchone():
        _logger.debug(f"Column {old_name} does not exist in {table}, skipping")
        return
    
    # Check if new column already exists
    cr.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = %s AND column_name = %s
    """, (table, new_name))
    
    if cr.fetchone():
        # New column exists - copy data and drop old
        _logger.info(f"Column {new_name} already exists in {table}, copying data from {old_name}")
        cr.execute(f"""
            UPDATE {table} SET {new_name} = {old_name}
            WHERE {old_name} IS NOT NULL AND ({new_name} IS NULL)
        """)
        cr.execute(f"ALTER TABLE {table} DROP COLUMN IF EXISTS {old_name}")
    else:
        # Rename column
        cr.execute(f"ALTER TABLE {table} RENAME COLUMN {old_name} TO {new_name}")
        _logger.info(f"Renamed column {old_name} to {new_name} in {table}")


def _update_ir_model_fields(cr, model, old_name, new_name):
    """Update field name in ir_model_fields."""
    cr.execute("""
        UPDATE ir_model_fields 
        SET name = %s 
        WHERE name = %s AND model = %s
    """, (new_name, old_name, model))
    if cr.rowcount:
        _logger.info(f"Updated ir_model_fields: {model}.{old_name} -> {new_name}")
