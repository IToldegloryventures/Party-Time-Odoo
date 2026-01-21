{
    "name": "Party Time Texas Dashboard",
    "summary": """
    Comprehensive BI Dashboard for Party Time Texas event management.
    Track events, sales, vendors, projects, and KPIs in real-time.
    """,
    "description": """
Party Time Texas Dashboard
==========================

A powerful business intelligence dashboard customized for Party Time Texas event management operations.

Features:
- Event performance tracking
- Sales and revenue analytics
- Vendor management metrics
- Project timeline visualization
- CRM pipeline insights
- Real-time KPI monitoring
- Interactive charts and graphs
- Customizable dashboard layouts
- Drill-down analysis
- Export to PDF

Based on Synconics BI Dashboard technology.
    """,
    "author": "Party Time Texas / Synconics Technologies Pvt. Ltd.",
    "website": "https://www.partytimetexas.com",
    "category": "Productivity",
    "version": "19.0.1.0.0",
    "depends": ["web", "mail", "project", "crm", "sale", "account", "ptt_business_core"],
    # "external_dependencies": {"python": ["imgkit"]},  # Removed - only needed for PDF export
    "assets": {
        "web.assets_backend": [
            "ptt_dashboard/static/src/lib/html2canvas.js",
            "ptt_dashboard/static/src/lib/jspdf.js",
            "ptt_dashboard/static/src/lib/amcharts/index.js",
            "ptt_dashboard/static/src/lib/amcharts/xy.js",
            "ptt_dashboard/static/src/lib/amcharts/exporting.js",
            "ptt_dashboard/static/src/lib/amcharts/map.js",
            "ptt_dashboard/static/src/lib/amcharts/worldLow.js",
            "ptt_dashboard/static/src/lib/amcharts/radar.js",
            "ptt_dashboard/static/src/lib/amcharts/flow.js",
            "ptt_dashboard/static/src/lib/amcharts/percent.js",
            "ptt_dashboard/static/src/lib/amcharts/hierarchy.js",
            "ptt_dashboard/static/src/lib/themes/**/*",
            "ptt_dashboard/static/src/lib/gridstack/**/*",
            "ptt_dashboard/static/src/js/dashboard_form_view.js",
            "ptt_dashboard/static/src/scss/dashboard_form_view.scss",
            "ptt_dashboard/static/src/js/form_dashboard_preview.js",
            "ptt_dashboard/static/src/xml/form_dashboard_preview.xml",
            "ptt_dashboard/static/src/js/fa_icon_widget.js",
            "ptt_dashboard/static/src/xml/fa_icon_widget.xml",
            "ptt_dashboard/static/src/js/dashboard_chart_wrapper.js",
            "ptt_dashboard/static/src/scss/dashboard_chart_wrapper.scss",
            "ptt_dashboard/static/src/xml/dashboard_chart_wrapper.xml",
            "ptt_dashboard/static/src/js/dashboard_amcharts.js",
            "ptt_dashboard/static/src/xml/dashboard_amcharts.xml",
            "ptt_dashboard/static/src/js/dashboard_selection/*",
            "ptt_dashboard/static/src/js/dashboard_selection/dashboard_selection.scss",
            "ptt_dashboard/static/src/components/**/*.js",
            "ptt_dashboard/static/src/components/**/*.xml",
            "ptt_dashboard/static/src/components/**/*.scss",
            "ptt_dashboard/static/src/components/KPILayouts/**/*",
            "ptt_dashboard/static/src/components/TileLayouts/**/*",
            "ptt_dashboard/static/src/components/ListView/ListView.scss",
            "ptt_dashboard/static/src/components/TodoView/TodoView.scss",
        ]
    },
    "cloc_exclude": [
        "static/src/lib/**/*",
    ],
    "data": [
        "security/dashboard_security.xml",
        "security/ir.model.access.csv",
        "data/mail_template.xml",
        "views/ir_ui_menu_views.xml",
        "wizard/dashboard_access_view.xml",
        "wizard/mail_compose_message_views.xml",
        "views/dashboard_view.xml",
        "data/dashboard_data.xml",
        "data/ptt_dashboards.xml",
        "data/ptt_dashboard_charts.xml",
        "views/dashboard_chart_view.xml",
        "views/res_users_view.xml",
    ],
    "images": ["static/description/main_screen.gif"],
    "license": "OPL-1",
    "uninstall_hook": "uninstall_hook",
    "installable": True,
    "application": True,
    "auto_install": False,
}
