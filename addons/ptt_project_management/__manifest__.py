{
    "name": "PTT Project Management",
    "version": "19.0.1.2.0",
    "summary": "Enhanced project management for Party Time Texas event execution",
    "description": """
Event Project Management Enhancement
====================================

This module provides:
* Stakeholder management for vendors and clients
* Timeline and milestone tracking
* Task and resource management for events
* Native project template integration via sale.order.type

NOTE: Project templates now use native Odoo project.project with is_template=True.
Templates are defined in ptt_business_core/data/project_template.xml (Corporate/Wedding/Social).
Event types link to templates via native_project_template_id field.

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
        "data/link_event_types_data.xml",
        "views/project_stakeholder_views.xml",
        "views/project_vendor_assignment_views.xml",
        "views/project_project_views.xml",
        "views/sale_order_type_views.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
}
