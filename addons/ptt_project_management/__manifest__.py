{
    "name": "PTT Project Management",
    "version": "19.0.1.0.0",
    "summary": "Enhanced project management for Party Time Texas event execution",
    "description": """
Event Project Management Enhancement
====================================

This module provides:
* Project templates for different event types
* Stakeholder management for vendors and clients
* Timeline and milestone tracking
* Task and resource management for events

Integrates with PTT Enhanced Sales for complete event lifecycle management.
    """,
    "category": "Project/Project",
    "author": "Party Time Texas",
    "license": "LGPL-3",
    "depends": [
        "project",
        "sale_project",
        "ptt_business_core",
        "ptt_enhanced_sales",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/project_templates_data.xml",
        "data/template_id_aliases.xml",
        "data/link_event_types_data.xml",
        "views/project_template_views.xml",
        "views/project_stakeholder_views.xml",
        "views/project_vendor_assignment_views.xml",
        "views/project_project_views.xml",
        "views/sale_order_type_views.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
}
