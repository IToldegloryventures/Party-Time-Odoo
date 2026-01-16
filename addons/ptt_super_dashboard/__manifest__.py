{
    "name": "PTT Super Dashboard",
    "version": "19.0.3.0.0",
    "summary": "Party Time Texas Super Dashboard - Enterprise dashboard system with customizable widgets",
    "description": """
        PTT Super Dashboard
        ===================
        Enterprise-grade dashboard system combining operational dashboards with
        customizable widget-based builders.

        Features:
        - Operational Dashboards: Home, Sales, Operations, Calendar tabs
        - Dashboard Builder: Create custom dashboards with drag-drop widgets
        - Widget System: KPI cards, charts (bar, line, pie), tables, metrics
        - REST API: Access dashboard data from external systems
        - Export: Excel and CSV export for all dashboard data
        - Pre-built Templates: Sales Performance, Project Status, Accounts Receivable

        Original Operational Dashboard Features:
        - Home: Agenda, My Work, Assigned Tasks, Personal To-Dos, Comments
        - Sales Dashboard: KPIs with click-through to native views
        - Event Calendar: Full calendar with status-based coloring

        Every item is clickable and opens the native Odoo form view.
    """,
    "category": "Customizations",
    "author": "Party Time Texas",
    "license": "LGPL-3",
    "depends": [
        "base",
        "web",
        "mail",
        "project",
        "crm",
        "sale",  # Required for sale.order model access
        "sale_management",
        "sale_crm",
        "account",
        "analytic",
        "sale_project",
        "ptt_business_core",  # Required for ptt_event_date and other PTT fields on crm.lead and project.project
    ],
    "external_dependencies": {
        "python": ["xlsxwriter"],  # Required for Excel export functionality
    },
    "data": [
        # Security (load first)
        "security/ptt_security.xml",
        "security/team_dashboard_security.xml",
        "security/ir.model.access.csv",
        # Data
        # NOTE: CRM stages removed - using stages from ptt_business_core instead
        # "data/crm_stages.xml",
        "data/dashboard_default_config.xml",
        "data/dashboard_templates.xml",  # Pre-built dashboard templates
        # Views & Actions (load before menus)
        "views/ptt_personal_todo_views.xml",
        "views/ptt_sales_rep_views.xml",
        "views/ptt_home_views.xml",
        "views/ptt_dashboard_views.xml",
        "views/ptt_dashboard_config_views.xml",
        "views/ptt_native_calendar_views.xml",
        # NOTE: ptt_native_kanban_views.xml DELETED - was creating standalone kanbans
        # that override native Odoo views. Use inherit_id pattern instead.
        "views/ptt_native_filter_views.xml",
        "data/ptt_search_filters.xml",
        # NOTE: ptt_dashboard_editor_views.xml removed in v19.0.1.0.3 - Phase 2 feature
        # Menus
        "views/ptt_dashboard_menu.xml",
        "views/ptt_dashboard_config_menu.xml",
    ],
    "assets": {
        "web.assets_backend": [
            # Styles
            "ptt_super_dashboard/static/src/home.scss",
            "ptt_super_dashboard/static/src/dashboard.scss",
            # Components (load XML templates before JS to ensure templates are registered)
            # NOTE: dashboard_back_button disabled - causes applyState errors on startup
            # "ptt_super_dashboard/static/src/components/dashboard_back_button.xml",
            # "ptt_super_dashboard/static/src/components/dashboard_back_button.js",
            "ptt_super_dashboard/static/src/components/home_navigation.xml",
            "ptt_super_dashboard/static/src/components/home_navigation.js",
            "ptt_super_dashboard/static/src/components/my_work_section.xml",
            "ptt_super_dashboard/static/src/components/my_work_section.js",
            "ptt_super_dashboard/static/src/components/assigned_tasks.xml",
            "ptt_super_dashboard/static/src/components/assigned_tasks.js",
            "ptt_super_dashboard/static/src/components/personal_todo.xml",
            "ptt_super_dashboard/static/src/components/personal_todo.js",
            "ptt_super_dashboard/static/src/components/assigned_comments.xml",
            "ptt_super_dashboard/static/src/components/assigned_comments.js",
            "ptt_super_dashboard/static/src/components/agenda_calendar.xml",
            "ptt_super_dashboard/static/src/components/agenda_calendar.js",
            "ptt_super_dashboard/static/src/components/event_calendar_full.xml",
            "ptt_super_dashboard/static/src/components/event_calendar_full.js",
            "ptt_super_dashboard/static/src/components/sales_dashboard.xml",
            "ptt_super_dashboard/static/src/components/sales_dashboard.js",
            "ptt_super_dashboard/static/src/components/operations_dashboard.xml",
            "ptt_super_dashboard/static/src/components/operations_dashboard.js",
            "ptt_super_dashboard/static/src/components/communication_dashboard.xml",
            "ptt_super_dashboard/static/src/components/communication_dashboard.js",
            "ptt_super_dashboard/static/src/components/dashboard_tasks_section.xml",
            "ptt_super_dashboard/static/src/components/dashboard_tasks_section.js",
            "ptt_super_dashboard/static/src/components/task_leaderboard.xml",
            "ptt_super_dashboard/static/src/components/task_leaderboard.js",
            "ptt_super_dashboard/static/src/components/metric_chart.xml",
            "ptt_super_dashboard/static/src/components/metric_chart.js",
            "ptt_super_dashboard/static/src/components/export_menu.xml",
            "ptt_super_dashboard/static/src/components/export_menu.js",
            # NOTE: dashboard_editor.js/xml removed in v19.0.1.0.3 - Phase 2 feature
            "ptt_super_dashboard/static/src/components/kpi_card.xml",
            "ptt_super_dashboard/static/src/components/kpi_card.js",
            "ptt_super_dashboard/static/src/components/dashboard_tabs.xml",
            "ptt_super_dashboard/static/src/components/dashboard_tabs.js",
            # Services (load after components so templates are available)
            "ptt_super_dashboard/static/src/home_service.js",
            "ptt_super_dashboard/static/src/dashboard_statistics_service.js",
            "ptt_super_dashboard/static/src/dashboard_back_button_service.js",
            # Controllers
            "ptt_super_dashboard/static/src/home_controller.xml",
            "ptt_super_dashboard/static/src/home_controller.js",
            # NOTE: dashboard_editor_controller.js/xml removed in v19.0.1.0.3 - Phase 2 feature
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}
