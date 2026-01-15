"""
Pre-migration script for PTT Business Core 19.0.1.2.4
Cleans up orphaned Studio customizations that reference non-existent fields.
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Clean up orphaned Studio views and fields."""
    if not version:
        return

    _logger.info("PTT 19.0.1.2.4: Cleaning up orphaned Studio customizations...")

    # 1. Remove orphaned ir.model.fields records for crm.lead (Studio fields)
    _logger.info("Removing orphaned Studio fields from ir.model.fields...")
    cr.execute("""
        DELETE FROM ir_model_fields
        WHERE model = 'crm.lead'
          AND name LIKE 'x_studio_%'
    """)
    deleted_fields = cr.rowcount
    _logger.info(f"Deleted {deleted_fields} orphaned Studio field records from crm.lead")

    # 2. Remove orphaned ir.model.fields records for project.project
    cr.execute("""
        DELETE FROM ir_model_fields
        WHERE model = 'project.project'
          AND name = 'x_plan2_id'
    """)
    deleted_project_fields = cr.rowcount
    _logger.info(f"Deleted {deleted_project_fields} orphaned project.project field records")

    # 3. Delete Studio view customizations that might reference orphaned fields
    _logger.info("Removing Studio view customizations...")
    cr.execute("""
        DELETE FROM ir_ui_view 
        WHERE name LIKE 'Odoo Studio:%' 
          AND model = 'crm.lead'
    """)
    deleted_views = cr.rowcount
    _logger.info(f"Deleted {deleted_views} Studio view customizations")

    _logger.info("PTT 19.0.1.2.4: Studio cleanup complete!")
