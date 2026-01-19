{
    "name": "PTT Vendor Management",
    "version": "19.0.4.0.0",
    "summary": "Vendor Management + Portal for Work Order Accept/Decline + Vendor Applications + RFQ",
    "description": """
        Vendor Management Application
        =============================
        
        Comprehensive vendor management system for Party Time Texas:
        - Vendor service types and categorization
        - Vendor tier system (Essentials/Classic/Premier)
        - Document management and compliance tracking
        - Vendor list views and search functionality
        
        Vendor Portal:
        - Vendors receive work order assignments via email
        - Vendors can accept/decline work orders from portal
        - Security-limited view (vendors only see their assignment, NOT customer pricing)
        - Project manager notifications on accept/decline
        
        Vendor Application Portal:
        - Public vendor application form
        - Invite wizard to send application invitations
        - Document upload during application
        - Application status tracking
        
        RFQ System (NEW):
        - Request for Quotes from multiple vendors
        - Vendor quote submission via portal
        - Winner selection workflow
        - Auto-close RFQs on closing date
        - Purchase order creation from selected quote
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
        "data/mail_template_work_order.xml",
        "data/mail_template_vendor_invite.xml",
        "data/mail_template_rfq.xml",
        "data/rfq_sequence.xml",
        "data/rfq_cron.xml",
        "data/server_actions.xml",
        "data/cron_jobs.xml",
        # Wizard views
        "wizard/ptt_vendor_invite_wizard_view.xml",
        # Views (configuration views first, then main views)
        "views/ptt_document_type_view.xml",
        "views/ptt_vendor_document_view.xml",
        "views/ptt_res_partner_view.xml",
        "views/ptt_vendor_list_view.xml",
        "views/ptt_vendor_onboarding_view.xml",
        "views/ptt_vendor_rfq_views.xml",
        "views/ptt_vendor_task_views.xml",
        "views/ptt_vendor_menus.xml",
        "views/vendor_portal_templates.xml",
        "views/vendor_application_templates.xml",
        "views/portal_rfq_templates.xml",
        # Portal view extensions (extends ptt_business_core project form)
        "views/ptt_project_vendor_portal_view.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
}
