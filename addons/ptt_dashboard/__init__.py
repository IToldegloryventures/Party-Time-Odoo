from . import models
from . import wizard


def post_init_hook(env):
    """Add all internal users to dashboard user group on install"""
    dashboard_user_group = env.ref('ptt_dashboard.group_dashboard_user', raise_if_not_found=False)
    if dashboard_user_group:
        internal_users = env['res.users'].sudo().search([
            ('share', '=', False),
            ('active', '=', True),
        ])
        dashboard_user_group.sudo().write({
            'users': [(4, user.id) for user in internal_users]
        })


def uninstall_hook(env):
    dashboards = env["dashboard.dashboard"].sudo().search([])
    dashboards.created_action_id.unlink()
    dashboards.created_menu_id.unlink()
