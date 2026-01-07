"""
Pre-migration script for PTT Business Core 19.0.1.2.4
Cleans up orphaned Studio customizations that reference non-existent fields.

The error occurs because Studio-created views in the database reference
fields like x_studio_inquiry_source that no longer exist in the model.
"""
import logging

_logger = logging.getLogger(__name__)

# Fields that were created by Studio but conflict with our custom fields
ORPHANED_STUDIO_FIELDS = [
    'x_studio_inquiry_source',
    'x_studio_event_type',
    'x_studio_event_date',
    'x_studio_end_time',
    'x_studio_end_time_1',
    'x_studio_boolean_field_297_1jckjk5dc',
    'x_studio_boolean_field_1vp_1jckie6sq',
]


def migrate(cr, version):
    """Clean up orphaned Studio views and fields."""
    if not version:
        return

    _logger.info("PTT 19.0.1.2.4: Cleaning up orphaned Studio customizations...")

    # 1. Remove orphaned ir.model.fields records for crm.lead
    _logger.info("Removing orphaned Studio fields from ir.model.fields...")
    cr.execute("""
        DELETE FROM ir_model_fields
        WHERE model = 'crm.lead'
          AND name IN %s
    """, (tuple(ORPHANED_STUDIO_FIELDS),))
    deleted_fields = cr.rowcount
    _logger.info(f"Deleted {deleted_fields} orphaned field records from ir.model.fields")

    # 2. Remove orphaned ir.model.fields records for project.project
    cr.execute("""
        DELETE FROM ir_model_fields
        WHERE model = 'project.project'
          AND name IN ('x_plan2_id',)
    """)
    deleted_project_fields = cr.rowcount
    _logger.info(f"Deleted {deleted_project_fields} orphaned project.project field records")

    # 3. Find and remove/reset Studio view customizations that reference orphaned fields
    _logger.info("Resetting Studio view customizations with orphaned field references...")
    
    # Find views that contain references to orphaned fields
    for field_name in ORPHANED_STUDIO_FIELDS:
        # Check ir.ui.view for any arch containing the field
        cr.execute("""
            SELECT id, name, model
            FROM ir_ui_view
            WHERE arch_db::text LIKE %s
              AND model = 'crm.lead'
        """, (f'%{field_name}%',))
        
        views_with_field = cr.fetchall()
        for view_id, view_name, model in views_with_field:
            _logger.warning(
                f"Found view {view_name} (id={view_id}, model={model}) "
                f"containing reference to orphaned field {field_name}"
            )
            
            # If it's a Studio customization, try to remove the field reference
            # We'll use a simple regex-based replacement approach
            cr.execute("""
                UPDATE ir_ui_view
                SET arch_db = regexp_replace(
                    arch_db::text,
                    '<field[^>]*name=["\']""" + field_name + """["\'][^>]*/?>',
                    '',
                    'gi'
                )::jsonb
                WHERE id = %s
            """, (view_id,))
            _logger.info(f"Cleaned field {field_name} from view {view_name} (id={view_id})")

    # 4. Also clean up any ir.ui.view.custom records (user-specific view customizations)
    _logger.info("Cleaning ir.ui.view.custom records with orphaned fields...")
    for field_name in ORPHANED_STUDIO_FIELDS:
        cr.execute("""
            UPDATE ir_ui_view_custom
            SET arch = regexp_replace(
                arch::text,
                '<field[^>]*name=["\']""" + field_name + """["\'][^>]*/?>',
                '',
                'gi'
            )
            WHERE arch::text LIKE %s
        """, (f'%{field_name}%',))
        updated = cr.rowcount
        if updated:
            _logger.info(f"Updated {updated} ir.ui.view.custom records to remove {field_name}")

    # 5. Drop the actual database columns if they still exist
    _logger.info("Dropping orphaned database columns from crm_lead...")
    for field_name in ORPHANED_STUDIO_FIELDS:
        try:
            cr.execute(f"""
                ALTER TABLE crm_lead DROP COLUMN IF EXISTS {field_name}
            """)
            _logger.info(f"Dropped column {field_name} from crm_lead (if existed)")
        except Exception as e:
            _logger.warning(f"Could not drop column {field_name}: {e}")

    _logger.info("PTT 19.0.1.2.4: Studio cleanup complete!")
