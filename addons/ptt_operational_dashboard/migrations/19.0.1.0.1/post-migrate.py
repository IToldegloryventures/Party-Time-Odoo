"""
Post-migration script to restore Odoo's default home action and clean up corrupted views.

This fixes:
1. The module incorrectly overrode base.action_client_base_menu causing blank screen
2. Corrupted search views cached in database with invalid <group expand> syntax
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Restore Odoo's default home action and clean corrupted views."""
    
    # === FIX 1: Restore default home action ===
    _logger.info("Restoring Odoo default home action...")
    
    cr.execute("""
        SELECT res_id FROM ir_model_data 
        WHERE module = 'base' 
        AND name = 'action_client_base_menu'
    """)
    result = cr.fetchone()
    
    if result:
        action_id = result[0]
        cr.execute(
            "UPDATE ir_act_client SET tag = %s, name = %s WHERE id = %s",
            ('menu', 'Menu', action_id)
        )
        _logger.info("Odoo default home action restored successfully (id=%s).", action_id)
    else:
        _logger.warning("Could not find base.action_client_base_menu to restore.")
    
    # === FIX 2: Delete corrupted search views so they reload fresh ===
    _logger.info("Cleaning up corrupted PTT search views...")
    
    # Delete the cached views that have invalid syntax
    # They will be recreated fresh from the corrected XML files
    cr.execute("""
        DELETE FROM ir_ui_view 
        WHERE model IN ('ptt.personal.todo', 'ptt.sales.commission')
        AND type = 'search'
    """)
    
    # Also delete any ir_model_data references to these views
    cr.execute("""
        DELETE FROM ir_model_data 
        WHERE module = 'ptt_operational_dashboard'
        AND name IN ('view_ptt_personal_todo_search', 'ptt_sales_commission_view_search')
    """)
    
    _logger.info("Corrupted views cleaned up. They will be recreated on module update.")

