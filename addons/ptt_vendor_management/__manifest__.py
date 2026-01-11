{
    "name": "PTT Vendor Management",
    "version": "19.0.1.0.0",
    "summary": "Standalone Vendor Management application for Party Time Texas",
    "description": """
        Vendor Management Application
        =============================
        
        Comprehensive vendor management system for Party Time Texas:
        - Vendor service tags and categorization
        - Vendor tier system (Gold/Silver/Bronze)
        - Document management and compliance tracking
        - Vendor list views and search functionality
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
    ],
    "data": [
        # Security (load first)
        "security/ir.model.access.csv",
        # Data (seed data)
        "data/ptt_document_type_data.xml",
        "data/ptt_vendor_service_tag_data.xml",
        # Views (configuration views first, then main views)
        "views/ptt_document_type_view.xml",
        "views/ptt_vendor_document_view.xml",
        "views/ptt_vendor_service_tag_view.xml",
        "views/ptt_res_partner_view.xml",
        "views/ptt_vendor_list_view.xml",
        "views/ptt_vendor_menus.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
}
