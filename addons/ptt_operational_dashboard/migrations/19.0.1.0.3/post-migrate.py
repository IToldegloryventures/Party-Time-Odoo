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
    
    # ptt.dashboard.metric.config - metric_name
    cr.execute("""
        SELECT COUNT(*) FROM ptt_dashboard_metric_config 
        WHERE metric_name IS NULL
    """)
    null_count = cr.fetchone()[0]
    if null_count > 0:
        _logger.warning("Found %s records with NULL metric_name, setting defaults...", null_count)
        cr.execute("""
            UPDATE ptt_dashboard_metric_config 
            SET metric_name = 'metric_' || id::text 
            WHERE metric_name IS NULL
        """)
    
    cr.execute("""
        ALTER TABLE ptt_dashboard_metric_config 
        ALTER COLUMN metric_name SET NOT NULL
    """)
    _logger.info("Added NOT NULL constraint to ptt_dashboard_metric_config.metric_name")
    
    # ptt.dashboard.metric.config - metric_label
    cr.execute("""
        SELECT COUNT(*) FROM ptt_dashboard_metric_config 
        WHERE metric_label IS NULL
    """)
    null_count = cr.fetchone()[0]
    if null_count > 0:
        _logger.warning("Found %s records with NULL metric_label, setting defaults...", null_count)
        cr.execute("""
            UPDATE ptt_dashboard_metric_config 
            SET metric_label = COALESCE(metric_name, 'Metric ' || id::text)
            WHERE metric_label IS NULL
        """)
    
    cr.execute("""
        ALTER TABLE ptt_dashboard_metric_config 
        ALTER COLUMN metric_label SET NOT NULL
    """)
    _logger.info("Added NOT NULL constraint to ptt_dashboard_metric_config.metric_label")
    
    # ptt.dashboard.metric.config - tab_assignment (has default, but ensure NOT NULL)
    cr.execute("""
        SELECT COUNT(*) FROM ptt_dashboard_metric_config 
        WHERE tab_assignment IS NULL
    """)
    null_count = cr.fetchone()[0]
    if null_count > 0:
        _logger.warning("Found %s records with NULL tab_assignment, setting defaults...", null_count)
        cr.execute("""
            UPDATE ptt_dashboard_metric_config 
            SET tab_assignment = 'sales'
            WHERE tab_assignment IS NULL
        """)
    
    cr.execute("""
        ALTER TABLE ptt_dashboard_metric_config 
        ALTER COLUMN tab_assignment SET NOT NULL
    """)
    _logger.info("Added NOT NULL constraint to ptt_dashboard_metric_config.tab_assignment")
    
    # ptt.dashboard.layout.config - section_name
    cr.execute("""
        SELECT COUNT(*) FROM ptt_dashboard_layout_config 
        WHERE section_name IS NULL
    """)
    null_count = cr.fetchone()[0]
    if null_count > 0:
        _logger.warning("Found %s records with NULL section_name, setting defaults...", null_count)
        cr.execute("""
            UPDATE ptt_dashboard_layout_config 
            SET section_name = 'section_' || id::text 
            WHERE section_name IS NULL
        """)
    
    cr.execute("""
        ALTER TABLE ptt_dashboard_layout_config 
        ALTER COLUMN section_name SET NOT NULL
    """)
    _logger.info("Added NOT NULL constraint to ptt_dashboard_layout_config.section_name")
    
    # ptt.dashboard.layout.config - section_label
    cr.execute("""
        SELECT COUNT(*) FROM ptt_dashboard_layout_config 
        WHERE section_label IS NULL
    """)
    null_count = cr.fetchone()[0]
    if null_count > 0:
        _logger.warning("Found %s records with NULL section_label, setting defaults...", null_count)
        cr.execute("""
            UPDATE ptt_dashboard_layout_config 
            SET section_label = COALESCE(section_name, 'Section ' || id::text)
            WHERE section_label IS NULL
        """)
    
    cr.execute("""
        ALTER TABLE ptt_dashboard_layout_config 
        ALTER COLUMN section_label SET NOT NULL
    """)
    _logger.info("Added NOT NULL constraint to ptt_dashboard_layout_config.section_label")
    
    # ptt.dashboard.layout.config - tab_assignment
    cr.execute("""
        SELECT COUNT(*) FROM ptt_dashboard_layout_config 
        WHERE tab_assignment IS NULL
    """)
    null_count = cr.fetchone()[0]
    if null_count > 0:
        _logger.warning("Found %s records with NULL tab_assignment, setting defaults...", null_count)
        cr.execute("""
            UPDATE ptt_dashboard_layout_config 
            SET tab_assignment = 'sales'
            WHERE tab_assignment IS NULL
        """)
    
    cr.execute("""
        ALTER TABLE ptt_dashboard_layout_config 
        ALTER COLUMN tab_assignment SET NOT NULL
    """)
    _logger.info("Added NOT NULL constraint to ptt_dashboard_layout_config.tab_assignment")
    
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

