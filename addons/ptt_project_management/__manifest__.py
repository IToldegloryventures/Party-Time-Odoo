{
    "name": "PTT Project Management",
    "version": "19.0.2.5.0",
    "summary": "Enhanced project management for Party Time Texas event execution",
    "description": """
Event Project Management Enhancement
====================================

This module provides:

**Core Features**
* Stakeholder management for vendors and clients
* Task and resource management for events
* Project views and enhancements for event planning

**Project Dashboard**
* KPI tiles: My Tasks, Projects, Active/Overdue/Today Tasks
* Interactive charts: Deadline pie, Stage doughnut, Project bar
* Paginated task and activity tables
* Drill-down to actual records
* Refresh button, auto-polling, date range filters
* Saved filter presets per user
* Quick task assignment from table
* Export to Excel functionality

NOTE: Project templates are defined in ptt_business_core/data/project_template.xml
(Corporate/Wedding/Social). Each Event Kickoff product directly links to its template.

Integrates with PTT Enhanced Sales for complete event lifecycle management.
    """,
    "category": "Project/Project",
    "author": "Party Time Texas",
    "license": "LGPL-3",
    "depends": [
        "project",
        "sale_project",
        "mail",  # Required for dashboard activities
        "ptt_business_core",
        "ptt_enhanced_sales",
    ],
    "external_dependencies": {"python": ["xlsxwriter"]},  # For Excel export
    "data": [
        "security/ir.model.access.csv",
        "views/project_stakeholder_views.xml",
        "views/project_vendor_assignment_views.xml",
        "views/project_project_views.xml",
        "views/dashboard_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "ptt_project_management/static/src/css/dashboard.css",
            "ptt_project_management/static/src/js/dashboard.js",
            "ptt_project_management/static/src/xml/dashboard.xml",
        ],
    },
    "installable": True,
    "application": True,
    "auto_install": False,
}
