"""
Pre-migration script for PTT Business Core 19.0.4.0.0

Removes redundant boolean service fields from crm.lead.
These fields duplicate functionality provided by ptt_service_line_ids (One2many).

Also cleans up orphaned x_customer_submission_notes field references from database.

Reference: https://www.odoo.com/documentation/19.0/contributing/development/coding_guidelines.html
- "Organize models logically and remove unnecessary fields to maintain a clean schema"
"""
import logging

_logger = logging.getLogger(__name__)

# Boolean service fields to remove from crm.lead
# These are redundant with ptt_service_line_ids One2many
FIELDS_TO_REMOVE = [
    'ptt_service_dj',
    'ptt_service_photovideo',
    'ptt_service_live_entertainment',
    'ptt_service_lighting',
    'ptt_service_decor',
    'ptt_service_venue_sourcing',
    'ptt_service_catering',
    'ptt_service_transportation',
    'ptt_service_rentals',
    'ptt_service_photobooth',
    'ptt_service_caricature',
    'ptt_service_casino',
    'ptt_service_staffing',
    # Also clean up orphaned x_ fields from previous versions
    'x_customer_submission_notes',
]


def _cleanup_orphaned_views(cr):
    """Remove views that reference non-existent fields.
    
    This cleans up database remnants from fields that were removed.
    Order matters: clean ir_model_data BEFORE ir_model_fields since data references fields.
    """
    _logger.info("Cleaning up orphaned fields and defunct modules...")
    
    # Mark ptt_contact_forms for removal if installed (module was deleted)
    cr.execute("""
        UPDATE ir_module_module 
        SET state = 'uninstalled'
        WHERE name = 'ptt_contact_forms' 
          AND state IN ('installed', 'to upgrade', 'to install')
    """)
    if cr.rowcount:
        _logger.info("  Marked ptt_contact_forms as uninstalled")
    
    _logger.info("Cleaning up orphaned x_customer_submission_notes field...")
    
    # 1. Clean up ir_model_data references FIRST (before deleting the field)
    cr.execute("""
        DELETE FROM ir_model_data 
        WHERE model = 'ir.model.fields' 
          AND (res_id = 19505 OR name LIKE '%x_customer_submission_notes%')
    """)
    if cr.rowcount:
        _logger.info("  Removed ir_model_data field references (count: %d)", cr.rowcount)
    
    # 2. Delete from ir_model_fields by name and by ID 19505
    cr.execute("""
        DELETE FROM ir_model_fields 
        WHERE (model = 'crm.lead' AND name = 'x_customer_submission_notes')
           OR id = 19505
    """)
    if cr.rowcount:
        _logger.info("  Removed x_customer_submission_notes from ir_model_fields (count: %d)", cr.rowcount)
    
    # 3. Find and delete ANY views referencing x_customer_submission_notes
    # This includes inherited views that might have been created via Studio
    cr.execute("""
        DELETE FROM ir_ui_view
        WHERE arch_db::text LIKE '%x_customer_submission_notes%'
    """)
    if cr.rowcount:
        _logger.info("  Deleted %d views referencing x_customer_submission_notes", cr.rowcount)
    
    # 4. Clean up ir_model_data pointing to deleted views
    cr.execute("""
        DELETE FROM ir_model_data 
        WHERE model = 'ir.ui.view'
          AND name LIKE '%x_customer_submission_notes%'
    """)
    if cr.rowcount:
        _logger.info("  Removed ir_model_data for deleted views (count: %d)", cr.rowcount)
    
    # 5. Drop column if exists
    cr.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'crm_lead' 
          AND column_name = 'x_customer_submission_notes'
    """)
    if cr.fetchone():
        cr.execute('ALTER TABLE crm_lead DROP COLUMN IF EXISTS "x_customer_submission_notes"')
        _logger.info("  Dropped column crm_lead.x_customer_submission_notes")


def migrate(cr, version):
    """Remove redundant boolean service fields from crm.lead.
    
    Uses savepoints to isolate each column drop operation for better error handling.
    Reference: https://www.odoo.com/documentation/19.0/developer/reference/backend/orm.html
    """
    if not version:
        return
    
    # First, clean up orphaned views that reference removed fields
    _cleanup_orphaned_views(cr)
    
    _logger.info("PTT Business Core 19.0.4.0.0: Removing redundant boolean service fields...")
    
    removed_count = 0
    
    for field_name in FIELDS_TO_REMOVE:
        # Use savepoint to isolate each operation
        cr.execute("SAVEPOINT remove_field_%s" % field_name.replace('.', '_'))
        try:
            # Check if column exists before trying to drop
            cr.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'crm_lead' 
                  AND column_name = %s
            """, (field_name,))
            
            if cr.fetchone():
                # Drop the column
                cr.execute('ALTER TABLE crm_lead DROP COLUMN IF EXISTS "%s"' % field_name)
                _logger.info("  Dropped column: crm_lead.%s", field_name)
                removed_count += 1
            else:
                _logger.debug("  Column already removed: crm_lead.%s", field_name)
            
            # Remove field from ir_model_fields
            cr.execute("""
                DELETE FROM ir_model_fields 
                WHERE model = 'crm.lead' 
                  AND name = %s
            """, (field_name,))
            
            cr.execute("RELEASE SAVEPOINT remove_field_%s" % field_name.replace('.', '_'))
            
        except Exception as e:
            cr.execute("ROLLBACK TO SAVEPOINT remove_field_%s" % field_name.replace('.', '_'))
            _logger.warning("  Error removing %s: %s", field_name, e)
    
    _logger.info("PTT Business Core 19.0.4.0.0: Removed %d boolean service fields", removed_count)
