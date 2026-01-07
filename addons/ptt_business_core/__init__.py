import logging
from . import models

_logger = logging.getLogger(__name__)


def pre_init_hook(cr):
    """
    Pre-init cleanup: Remove orphaned field metadata before module upgrade.
    This runs BEFORE the module upgrade to prevent errors during upgrade.
    
    NOTE: In Odoo 19, pre_init_hook receives 'cr' (database cursor), not 'env'.
    We must use raw SQL or create environment manually.
    """
    _logger.info("PTT Business Core: Running pre_init_hook cleanup")
    try:
        # Use raw SQL since we only have cursor at pre_init stage
        # Check if ir_model_fields table exists and clean orphaned fields
        cr.execute("""
            DELETE FROM ir_model_fields 
            WHERE name = 'x_secondary_salesperson_id' 
            AND model IN ('project.project', 'crm.lead')
            RETURNING id
        """)
        deleted_ids = cr.fetchall()
        if deleted_ids:
            count = len(deleted_ids)
            _logger.info(f"PTT Business Core: Deleted {count} orphaned x_secondary_salesperson_id field(s)")
        else:
            _logger.info("PTT Business Core: No orphaned fields found (clean)")
    except Exception as e:
        _logger.error(f"PTT Business Core: Error in pre_init_hook: {e}", exc_info=True)
        # Don't fail the upgrade if cleanup fails - just log and continue


