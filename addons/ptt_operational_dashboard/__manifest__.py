{
    "name": "PTT Operational Dashboard",
    "version": "19.0.1.0.3",
    "summary": "Party Time Texas Home Hub - unified view into all Odoo apps",
    "description": """
        PTT Home Dashboard Hub
        ======================
        A smart aggregation layer providing a personalized "at-a-glance" view with 
        one-click access to all standard Odoo apps.
        
        Features:
        - Home: Agenda, My Work, Assigned Tasks, Personal To-Dos, Comments
        - Sales Dashboard: KPIs with click-through to native views
        - Commission Dashboard: Sales rep performance tracking
        - Event Calendar: Full calendar with status-based coloring
        
        Every item is clickable and opens the native Odoo form view.
        
        Data Sources (no duplication):
        - project.task (My Work, Assigned Tasks)
        - project.project (Agenda, Event Calendar)
        - crm.lead (Lead stages, linked opportunities)
        - sale.order (Sales Dashboard quotes)
        - account.move (Outstanding payments)
        - mail.message (Assigned Comments)
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
        "sale_management",
        "sale_crm",
        "account",
        "analytic",
        "sale_project",
    ],
    "data": [
        # Security (load first)
        "security/ptt_security.xml",
        "security/ir.model.access.csv",
        # Data (CRM Stages)
        "data/crm_stages.xml",
        "data/dashboard_default_config.xml",
        # Views & Actions (load before menus)
        "views/ptt_personal_todo_views.xml",
        "views/ptt_sales_rep_views.xml",
        "views/ptt_sales_commission_views.xml",
        "views/ptt_home_views.xml",
        "views/ptt_dashboard_views.xml",
        "views/ptt_dashboard_config_views.xml",
        # NOTE: ptt_dashboard_editor_views.xml removed in v19.0.1.0.3 - Phase 2 feature
        # Menus
        "views/ptt_dashboard_menu.xml",
        "views/ptt_dashboard_config_menu.xml",
    ],
    "assets": {
        "web.assets_backend": [
            # Styles
            "ptt_operational_dashboard/static/src/home.scss",
            "ptt_operational_dashboard/static/src/dashboard.scss",
            # Components (load XML templates before JS to ensure templates are registered)
            # DashboardBackButton template - load from xml directory first to ensure registration
            "ptt_operational_dashboard/static/src/xml/dashboard_templates.xml",
            "ptt_operational_dashboard/static/src/components/dashboard_back_button.js",
            "ptt_operational_dashboard/static/src/components/home_navigation.xml",
            "ptt_operational_dashboard/static/src/components/home_navigation.js",
            "ptt_operational_dashboard/static/src/components/my_work_section.xml",
            "ptt_operational_dashboard/static/src/components/my_work_section.js",
            "ptt_operational_dashboard/static/src/components/assigned_tasks.xml",
            "ptt_operational_dashboard/static/src/components/assigned_tasks.js",
            "ptt_operational_dashboard/static/src/components/personal_todo.xml",
            "ptt_operational_dashboard/static/src/components/personal_todo.js",
            "ptt_operational_dashboard/static/src/components/assigned_comments.xml",
            "ptt_operational_dashboard/static/src/components/assigned_comments.js",
            "ptt_operational_dashboard/static/src/components/agenda_calendar.xml",
            "ptt_operational_dashboard/static/src/components/agenda_calendar.js",
            "ptt_operational_dashboard/static/src/components/event_calendar_full.xml",
            "ptt_operational_dashboard/static/src/components/event_calendar_full.js",
            "ptt_operational_dashboard/static/src/components/sales_dashboard.xml",
            "ptt_operational_dashboard/static/src/components/sales_dashboard.js",
            "ptt_operational_dashboard/static/src/components/operations_dashboard.xml",
            "ptt_operational_dashboard/static/src/components/operations_dashboard.js",
            "ptt_operational_dashboard/static/src/components/communication_dashboard.xml",
            "ptt_operational_dashboard/static/src/components/communication_dashboard.js",
            "ptt_operational_dashboard/static/src/components/dashboard_tasks_section.xml",
            "ptt_operational_dashboard/static/src/components/dashboard_tasks_section.js",
            "ptt_operational_dashboard/static/src/components/task_leaderboard.xml",
            "ptt_operational_dashboard/static/src/components/task_leaderboard.js",
            "ptt_operational_dashboard/static/src/components/metric_chart.xml",
            "ptt_operational_dashboard/static/src/components/metric_chart.js",
            "ptt_operational_dashboard/static/src/components/export_menu.xml",
            "ptt_operational_dashboard/static/src/components/export_menu.js",
            # NOTE: dashboard_editor.js/xml removed in v19.0.1.0.3 - Phase 2 feature
            "ptt_operational_dashboard/static/src/components/kpi_card.xml",
            "ptt_operational_dashboard/static/src/components/kpi_card.js",
            "ptt_operational_dashboard/static/src/components/dashboard_tabs.xml",
            "ptt_operational_dashboard/static/src/components/dashboard_tabs.js",
            # Services (load after components so templates are available)
            "ptt_operational_dashboard/static/src/home_service.js",
            "ptt_operational_dashboard/static/src/dashboard_statistics_service.js",
            "ptt_operational_dashboard/static/src/dashboard_back_button_service.js",
            # Controllers
            "ptt_operational_dashboard/static/src/home_controller.xml",
            "ptt_operational_dashboard/static/src/home_controller.js",
            # NOTE: dashboard_editor_controller.js/xml removed in v19.0.1.0.3 - Phase 2 feature
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}
