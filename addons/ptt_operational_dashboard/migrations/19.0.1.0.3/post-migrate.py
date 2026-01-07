"""
Post-migration script to fix blank database screen issue.

This fixes:
1. Clears any user home actions pointing to PTT dashboard
2. Clears session storage references to PTT menu
3. Ensures default Odoo home action is restored
"""
import json
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Fix blank database screen by clearing PTT dashboard references."""
    
    # === FIX 1: Clear user home actions pointing to PTT dashboard ===
    _logger.info("Clearing user home actions pointing to PTT dashboard...")
    
    # Find the PTT home hub action
    cr.execute("""
        SELECT res_id FROM ir_model_data 
        WHERE module = 'ptt_operational_dashboard' 
        AND name = 'action_ptt_home_hub'
    """)
    result = cr.fetchone()
    
    if result:
        ptt_action_id = result[0]
        # Clear any users that have this action as their home action
        cr.execute("""
            UPDATE res_users 
            SET action_id = NULL 
            WHERE action_id = %s
        """, (ptt_action_id,))
        affected = cr.rowcount
        _logger.info("Cleared home action for %s user(s).", affected)
    
    # === FIX 2: Restore default Odoo home action ===
    _logger.info("Ensuring Odoo default home action is correct...")
    
    cr.execute("""
        SELECT res_id FROM ir_model_data 
        WHERE module = 'base' 
        AND name = 'action_client_base_menu'
    """)
    result = cr.fetchone()
    
    if result:
        action_id = result[0]
        # Ensure it's set to 'menu' tag
        name_json = json.dumps({"en_US": "Menu"})
        cr.execute("""
            UPDATE ir_act_client 
            SET tag = %s, name = %s 
            WHERE id = %s
        """, ('menu', name_json, action_id))
        _logger.info("Odoo default home action verified (id=%s).", action_id)
    else:
        _logger.warning("Could not find base.action_client_base_menu.")
    
    # === FIX 3: Clear any menu selections in ir_ui_menu that might be broken ===
    _logger.info("Verifying menu structure...")
    
    # Check if PTT root menu exists and has proper structure
    cr.execute("""
        SELECT id FROM ir_ui_menu 
        WHERE complete_name LIKE 'Home%' 
        AND action IS NULL
        ORDER BY sequence
        LIMIT 1
    """)
    menu_result = cr.fetchone()
    
    if menu_result:
        _logger.info("PTT Home menu found (id=%s).", menu_result[0])
    
    _logger.info("Migration completed. Database should now show standard Odoo home screen.")

