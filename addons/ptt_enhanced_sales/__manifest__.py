{
    "name": "PTT Enhanced Sales",
    "version": "19.0.1.0.0",
    "summary": "Event type management and quote revisions for Party Time Texas",
    "description": """
Event Management Sales Enhancement
==================================

This module provides:
* Event type classification and management
* Quote revision tracking for event planning
* Automated event workflow setup
* Integration with project templates

Designed specifically for Party Time Texas event management workflow.
    """,
    "category": "Sales/Sales",
    "author": "Party Time Texas",
    "license": "LGPL-3",
    "depends": [
        "sale",
        "sale_project",
        "crm",
        "project",
        "account",
        "ptt_business_core",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/event_types_data.xml",
        "data/legacy_event_type_aliases.xml",
        "views/sale_order_type_views.xml",
        "views/sale_order_views.xml",
        "views/crm_lead_views.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
}
