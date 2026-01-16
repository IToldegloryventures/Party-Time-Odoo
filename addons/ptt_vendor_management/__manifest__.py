{
    "name": "PTT Vendor Management",
    "version": "19.0.3.1.0",  # Fix: Button to populate document lines for existing vendors
    "summary": "Vendor Management + Portal for Work Order Accept/Decline",
    "description": """
        Vendor Management Application
        =============================
        
        Comprehensive vendor management system for Party Time Texas:
        - Vendor service tags and categorization
        - Vendor tier system (Essentials/Classic/Premier)
        - Document management and compliance tracking
        - Vendor list views and search functionality
        
        Vendor Portal (NEW):
        - Vendors receive work order assignments via email
        - Vendors can accept/decline work orders from portal
        - Security-limited view (vendors only see their assignment, NOT customer pricing)
        - Project manager notifications on accept/decline
    """,
    "category": "Sales",
    "author": "Party Time Texas",
    "license": "LGPL-3",
    "depends": [
        "base",
        "contacts",
        "mail",
        "portal",
        "purchase",
        "project",  # Required for project view references
        "ptt_business_core",  # Has ptt.project.vendor.assignment model
    ],
    "data": [
        # Security (load first)
        "security/ir.model.access.csv",
        "security/vendor_portal_rules.xml",
        # Data (seed data)
        "data/ptt_document_type_data.xml",
        "data/ptt_vendor_service_tag_data.xml",
        "data/mail_template_work_order.xml",
      "data/server_actions.xml",
        # Views (configuration views first, then main views)
        "views/ptt_document_type_view.xml",
        "views/ptt_vendor_document_view.xml",
        "views/ptt_vendor_service_tag_view.xml",
        "views/ptt_res_partner_view.xml",
        "views/ptt_vendor_list_view.xml",
        "views/ptt_vendor_menus.xml",
        "views/vendor_portal_templates.xml",
        # Portal view extensions (extends ptt_business_core project form)
        "views/ptt_project_vendor_portal_view.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
}
