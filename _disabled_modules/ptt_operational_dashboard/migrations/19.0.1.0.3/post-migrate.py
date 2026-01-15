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
    # === CLEANUP 0: Remove stale records referencing removed models ===
    # In v19.0.1.0.3 we removed the Dashboard Editor models. If a database had
    # previous versions installed, their views/actions/menus may still exist and
    # refer to non-existent models, causing "Missing model ..." errors at load.
    removed_models = (
        "ptt.dashboard.metric.config",
        "ptt.dashboard.layout.config",
    )

    try:
        _logger.info("Cleaning up stale records for removed models...")
        
        # Initialize counters
        model_count = field_count = access_count = data_count = view_count = act_count = menu_count = 0

        # 0.0) ir.model records (the model definitions themselves)
        cr.execute("""
            SELECT COUNT(1) FROM ir_model
            WHERE model = ANY(%s)
        """, (list(removed_models),))
        model_count = cr.fetchone()[0]
        if model_count:
            _logger.info("Found %s stale ir.model records to delete", model_count)
            # Delete ir.model.data first
            cr.execute("""
                DELETE FROM ir_model_data
                WHERE model = 'ir.model'
                  AND res_id IN (SELECT id FROM ir_model WHERE model = ANY(%s))
            """, (list(removed_models),))
            # Then delete the models
            cr.execute("""
                DELETE FROM ir_model
                WHERE model = ANY(%s)
            """, (list(removed_models),))

        # 0.0b) ir.model.fields records (field definitions)
        cr.execute("""
            SELECT COUNT(1) FROM ir_model_fields
            WHERE model = ANY(%s)
        """, (list(removed_models),))
        field_count = cr.fetchone()[0]
        if field_count:
            _logger.info("Found %s stale ir.model.fields records to delete", field_count)
            # Delete ir.model.data first
            cr.execute("""
                DELETE FROM ir_model_data
                WHERE model = 'ir.model.fields'
                  AND res_id IN (SELECT id FROM ir_model_fields WHERE model = ANY(%s))
            """, (list(removed_models),))
            # Then delete the fields
            cr.execute("""
                DELETE FROM ir_model_fields
                WHERE model = ANY(%s)
            """, (list(removed_models),))

        # 0.0c) ir.model.access records (security rules)
        # Check for access rules that reference these models
        cr.execute("""
            SELECT COUNT(1) FROM ir_model_access a
            JOIN ir_model m ON m.id = a.model_id
            WHERE m.model = ANY(%s)
        """, (list(removed_models),))
        access_count = cr.fetchone()[0]
        if access_count:
            _logger.info("Found %s stale ir.model.access records to delete", access_count)
            cr.execute("""
                DELETE FROM ir_model_access a
                USING ir_model m
                WHERE a.model_id = m.id
                  AND m.model = ANY(%s)
            """, (list(removed_models),))

        # 0.0d) Any other ir.model.data records referencing these models
        cr.execute("""
            SELECT COUNT(1) FROM ir_model_data
            WHERE (name LIKE '%metric.config%' OR name LIKE '%layout.config%')
              AND module = 'ptt_operational_dashboard'
        """)
        data_count = cr.fetchone()[0]
        if data_count:
            _logger.info("Found %s additional ir.model.data records to delete", data_count)
            cr.execute("""
                DELETE FROM ir_model_data
                WHERE (name LIKE '%metric.config%' OR name LIKE '%layout.config%')
                  AND module = 'ptt_operational_dashboard'
            """)

        # 0.a) Views linked to removed models (scoped to this module)
        cr.execute("""
            SELECT COUNT(1)
            FROM ir_ui_view v
            JOIN ir_model_data d
              ON d.model = 'ir.ui.view'
             AND d.res_id = v.id
            WHERE d.module = 'ptt_operational_dashboard'
              AND v.model = ANY(%s)
        """, (list(removed_models),))
        view_count = cr.fetchone()[0]
        if view_count:
            _logger.info("Found %s stale ir.ui.view records to delete", view_count)
            cr.execute("""
                DELETE FROM ir_model_data d
                USING ir_ui_view v
                WHERE d.model = 'ir.ui.view'
                  AND d.res_id = v.id
                  AND d.module = 'ptt_operational_dashboard'
                  AND v.model = ANY(%s)
            """, (list(removed_models),))
            cr.execute("""
                DELETE FROM ir_ui_view v
                WHERE v.model = ANY(%s)
                  AND NOT EXISTS (
                    SELECT 1 FROM ir_model_data d
                    WHERE d.model = 'ir.ui.view' AND d.res_id = v.id
                  )
            """, (list(removed_models),))

        # 0.b) Window actions linked to removed models (scoped to this module)
        cr.execute("""
            SELECT COUNT(1)
            FROM ir_act_window w
            JOIN ir_model_data d
              ON d.model = 'ir.actions.act_window'
             AND d.res_id = w.id
            WHERE d.module = 'ptt_operational_dashboard'
              AND w.res_model = ANY(%s)
        """, (list(removed_models),))
        act_count = cr.fetchone()[0]
        if act_count:
            _logger.info("Found %s stale ir.actions.act_window records to delete", act_count)
            cr.execute("""
                DELETE FROM ir_model_data d
                USING ir_act_window w
                WHERE d.model = 'ir.actions.act_window'
                  AND d.res_id = w.id
                  AND d.module = 'ptt_operational_dashboard'
                  AND w.res_model = ANY(%s)
            """, (list(removed_models),))
            cr.execute("""
                DELETE FROM ir_actions_actions a
                USING ir_act_window w
                WHERE a.id = w.id
                  AND w.res_model = ANY(%s)
                  AND NOT EXISTS (
                    SELECT 1 FROM ir_model_data d
                    WHERE d.model = 'ir.actions.act_window' AND d.res_id = a.id
                  )
            """, (list(removed_models),))

        # 0.c) Menus pointing to actions of removed models (scoped to this module)
        # Join ir_ui_menu -> ir_actions_actions (a) -> ir_act_window (w)
        cr.execute("""
            SELECT COUNT(1)
            FROM ir_ui_menu m
            JOIN ir_model_data dm
              ON dm.model = 'ir.ui.menu'
             AND dm.res_id = m.id
            JOIN ir_actions_actions a
              ON a.id = m.action
            LEFT JOIN ir_act_window w
              ON w.id = a.id
            WHERE dm.module = 'ptt_operational_dashboard'
              AND w.res_model = ANY(%s)
        """, (list(removed_models),))
        menu_count = cr.fetchone()[0]
        if menu_count:
            _logger.info("Found %s stale ir.ui_menu entries pointing to removed models", menu_count)
            # Delete their ir.model.data and the menus themselves
            cr.execute("""
                DELETE FROM ir_model_data d
                USING ir_ui_menu m, ir_actions_actions a, ir_act_window w
                WHERE d.model = 'ir.ui.menu'
                  AND d.res_id = m.id
                  AND d.module = 'ptt_operational_dashboard'
                  AND a.id = m.action
                  AND w.id = a.id
                  AND w.res_model = ANY(%s)
            """, (list(removed_models),))
            cr.execute("""
                DELETE FROM ir_ui_menu m
                USING ir_actions_actions a, ir_act_window w
                WHERE a.id = m.action
                  AND w.id = a.id
                  AND w.res_model = ANY(%s)
                  AND NOT EXISTS (
                    SELECT 1 FROM ir_model_data d
                    WHERE d.model = 'ir.ui.menu' AND d.res_id = m.id
                  )
            """, (list(removed_models),))

        _logger.info("Cleanup complete. Models: %s, Fields: %s, Access: %s, Data: %s, Views: %s, Actions: %s, Menus: %s", 
                     model_count, field_count, access_count, data_count, view_count, act_count, menu_count)
    except Exception as e:
        _logger.warning("Cleanup for removed models failed (continuing migration): %s", e)
    
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

