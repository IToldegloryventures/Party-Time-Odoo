import logging
from . import models

_logger = logging.getLogger(__name__)


def pre_init_hook(env):
    """
    Pre-init cleanup: Remove orphaned field metadata before module upgrade.
    This runs BEFORE the module upgrade to prevent errors during upgrade.
    """
    _logger.info("PTT Business Core: Running pre_init_hook cleanup")
    try:
        # Use with_for_update=False to avoid lock issues
        FieldModel = env['ir.model.fields'].with_context(active_test=False)
        orphaned_fields = FieldModel.search([
            ('name', '=', 'x_secondary_salesperson_id'),
            ('model', 'in', ['project.project', 'crm.lead'])
        ])
        if orphaned_fields:
            count = len(orphaned_fields)
            _logger.info(f"PTT Business Core: Found {count} orphaned x_secondary_salesperson_id field(s) to delete")
            orphaned_fields.unlink()
            # Don't commit - Odoo manages transactions around hooks
            _logger.info("PTT Business Core: Successfully deleted orphaned field metadata")
        else:
            _logger.info("PTT Business Core: No orphaned fields found (clean)")
    except Exception as e:
        _logger.error(f"PTT Business Core: Error in pre_init_hook: {e}", exc_info=True)
        # Don't fail the upgrade if cleanup fails - just log and continue


def post_init_hook(env):
    """
    Post-init cleanup: Remove orphaned field metadata after module upgrade.
    This runs AFTER the module upgrade as a safety net.
    CRITICAL: This function must not raise exceptions or the registry will fail to load.
    """
    _logger.info("PTT Business Core: Running post_init_hook cleanup")
    try:
        # Use with_context to avoid any active filtering issues
        FieldModel = env['ir.model.fields'].with_context(active_test=False)
        orphaned_fields = FieldModel.search([
            ('name', '=', 'x_secondary_salesperson_id'),
            ('model', 'in', ['project.project', 'crm.lead'])
        ])
        if orphaned_fields:
            count = len(orphaned_fields)
            _logger.warning(f"PTT Business Core: Found {count} orphaned x_secondary_salesperson_id field(s) after upgrade - deleting")
            orphaned_fields.unlink()
            # Don't commit - Odoo manages transactions around hooks
            _logger.info("PTT Business Core: Successfully deleted orphaned field metadata in post_init")
        else:
            _logger.info("PTT Business Core: No orphaned fields found in post_init (clean)")
    except Exception as e:
        # CRITICAL: Log but don't raise - any exception here will crash registry load
        _logger.error(f"PTT Business Core: Error in post_init_hook (non-fatal): {e}", exc_info=True)
        # Don't rollback - let Odoo handle transaction management
        # Just log and continue - this is cleanup, not critical functionality


