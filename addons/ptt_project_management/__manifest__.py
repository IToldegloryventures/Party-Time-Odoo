{
    "name": "PTT Project Management",
    "version": "19.0.2.0.0",
    "summary": "Enhanced project management for Party Time Texas event execution",
    "description": """
Event Project Management Enhancement
====================================

This module provides:

**Core Features**
* Stakeholder management for vendors and clients
* Task and resource management for events
* Project views and enhancements for event planning

**Task Deadline Calculation**
* Automatic deadline calculation from Sale Order dates
* Configurable offsets from SO confirmation or event date
* Parent task blocking until subtasks complete

**Project Dashboard**
* KPI tiles: My Tasks, Projects, Active/Overdue/Today Tasks
* Interactive charts: Deadline pie, Stage doughnut, Project bar
* Paginated task and activity tables
* Drill-down to actual records

**Event Calendar**
* Calendar view by event date
* Color-coded by event type
* Quick filters for upcoming events

**Document Management**
* Simple attachment linking to projects and tasks
* Centralized Documents menu in Projects app

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
        "calendar",
        "mail",
        "ptt_business_core",
        "ptt_enhanced_sales",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/project_stakeholder_views.xml",
        "views/project_vendor_assignment_views.xml",
        "views/project_project_views.xml",
        "views/event_calendar_views.xml",
        "views/ir_attachment_views.xml",
        "views/dashboard_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            # Chart.js for dashboard charts
            "https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js",
            # Dashboard styles
            "ptt_project_management/static/src/css/dashboard.css",
            # Dashboard Owl component
            "ptt_project_management/static/src/js/dashboard.js",
            # Dashboard QWeb template
            "ptt_project_management/static/src/xml/dashboard.xml",
        ],
    },
    "installable": True,
    "application": True,
    "auto_install": False,
}
