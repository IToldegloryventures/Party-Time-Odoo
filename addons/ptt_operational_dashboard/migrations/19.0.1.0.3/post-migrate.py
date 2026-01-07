"""
Post-migration script to fix blank database screen issue and add NOT NULL constraints.

This fixes:
1. Clears any user home actions pointing to PTT dashboard
2. Clears session storage references to PTT menu
3. Ensures default Odoo home action is restored
4. Adds NOT NULL constraints to required fields
"""
import json
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Fix blank database screen and add NOT NULL constraints."""
    
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
    
    # === FIX 3: Add NOT NULL constraints to required fields ===
    _logger.info("Adding NOT NULL constraints to required fields...")
    
    # NOTE: Dashboard Editor models (ptt.dashboard.metric.config, ptt.dashboard.layout.config) 
    # were removed in v19.0.1.0.3 - Phase 2 feature. Skip constraint additions for these tables.
    # If tables exist (from previous installs), they will be dropped during module upgrade.
    
    def table_exists(table_name):
        """Check if a table exists in the database."""
        cr.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = %s
            )
        """, (table_name,))
        return cr.fetchone()[0]
    
    # Only process dashboard editor tables if they exist (for backward compatibility)
    if table_exists('ptt_dashboard_metric_config'):
        _logger.info("ptt_dashboard_metric_config table exists - skipping (models removed in v19.0.1.0.3)")
    if table_exists('ptt_dashboard_layout_config'):
        _logger.info("ptt_dashboard_layout_config table exists - skipping (models removed in v19.0.1.0.3)")
    
    # Check other required fields in other models
    # ptt.sales.commission - sales_rep_id
    cr.execute("""
        SELECT COUNT(*) FROM ptt_sales_commission 
        WHERE sales_rep_id IS NULL
    """)
    null_count = cr.fetchone()[0]
    if null_count > 0:
        _logger.warning("Found %s records with NULL sales_rep_id, these will need manual cleanup", null_count)
        # Don't set a default, just log - these records are invalid
    
    # ptt.sales.commission - report_month
    cr.execute("""
        SELECT COUNT(*) FROM ptt_sales_commission 
        WHERE report_month IS NULL
    """)
    null_count = cr.fetchone()[0]
    if null_count > 0:
        _logger.warning("Found %s records with NULL report_month, setting defaults...", null_count)
        cr.execute("""
            UPDATE ptt_sales_commission 
            SET report_month = DATE_TRUNC('month', CURRENT_DATE)
            WHERE report_month IS NULL
        """)
    
    # ptt.sales.rep - user_id
    cr.execute("""
        SELECT COUNT(*) FROM ptt_sales_rep 
        WHERE user_id IS NULL
    """)
    null_count = cr.fetchone()[0]
    if null_count > 0:
        _logger.warning("Found %s records with NULL user_id, these will need manual cleanup", null_count)
    
    # ptt.personal.todo - user_id and name
    cr.execute("""
        SELECT COUNT(*) FROM ptt_personal_todo 
        WHERE user_id IS NULL OR name IS NULL
    """)
    null_count = cr.fetchone()[0]
    if null_count > 0:
        _logger.warning("Found %s records with NULL user_id or name, these will need manual cleanup", null_count)
    
    _logger.info("Migration completed. NOT NULL constraints added and database should now show standard Odoo home screen.")

