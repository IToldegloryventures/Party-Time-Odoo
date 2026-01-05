"""
Post-migration script to restore Odoo's default home action.

This fixes the issue where the module incorrectly overrode base.action_client_base_menu
causing a blank screen on login.
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Restore Odoo's default home action to 'menu' tag."""
    _logger.info("Restoring Odoo default home action...")
    
    # Reset the base home action to Odoo's default
    cr.execute("""
        UPDATE ir_act_client
        SET tag = 'menu', name = 'Menu'
        WHERE id = (
            SELECT res_id FROM ir_model_data 
            WHERE module = 'base' 
            AND name = 'action_client_base_menu'
        )
    """)
    
    _logger.info("Odoo default home action restored successfully.")

