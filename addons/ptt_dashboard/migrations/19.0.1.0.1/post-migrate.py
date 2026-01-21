# -*- coding: utf-8 -*-
"""
Migration script to fix dashboard security rules.
This runs automatically when the module is upgraded to version 19.0.1.0.1+
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """
    Update the dashboard access rule to include group_ids check.
    This is needed because the rule is in a noupdate="1" block.
    """
    if not version:
        # Fresh install, no migration needed
        return

    _logger.info("Migrating ptt_dashboard: Updating dashboard access rules...")

    # Update the dashboard user rule to check group_ids
    new_domain = """[
        '|', '|', '|',
            ('user_ids', 'in', user.ids),
            ('user_ids', '=', False),
            '&',
                ('access_by', '=', 'access_group'),
                ('group_ids', 'in', user.group_ids.ids),
        '|',
            ('company_id', '=', False),
            ('company_id', 'in', company_ids)
    ]"""

    cr.execute("""
        UPDATE ir_rule
        SET domain_force = %s
        WHERE name = 'Dashboard'
        AND model_id = (SELECT id FROM ir_model WHERE model = 'dashboard.dashboard')
    """, (new_domain,))

    _logger.info("✅ Dashboard access rule updated successfully!")
