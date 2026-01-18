{
    "name": "PTT Vendor Management",
    "version": "19.0.1.0.0",
    "summary": "Vendor portal, RFQ, and coordination for Party Time Texas",
    "description": """
Vendor Management Portal
========================

This module provides comprehensive vendor management including:
* Vendor RFQ (Request for Quote) system for event services
* Vendor portal access to view and respond to service requests
* Quote comparison and approval workflow
* Vendor registration and onboarding
* Document sharing for event coordination
* Performance tracking and vendor ratings
* Email notifications for RFQs and assignments

Inspired by Cybrosys Technologies vendor_portal_odoo module,
adapted for Party Time Texas event management workflow.
    """,
    "category": "Website/Website",
    "author": "Party Time Texas",
    "license": "LGPL-3",
    "depends": [
        "portal",
        "mail",
        "project",
        "crm",
        "ptt_business_core",
        "ptt_project_management",
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/vendor_portal_security.xml",
        "data/vendor_rfq_sequence.xml",
        "data/vendor_mail_templates.xml",
        "wizard/register_vendor_views.xml",
        "views/vendor_rfq_views.xml",
        "views/res_partner_views.xml",
        "views/portal_templates.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "ptt_vendor_management/static/src/scss/vendor_portal.scss",
        ],
    },
    "installable": True,
    "application": True,
    "auto_install": False,
}
