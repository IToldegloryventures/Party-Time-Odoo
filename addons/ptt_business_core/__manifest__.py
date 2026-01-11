{
    "name": "PTT Business Core",
    "version": "19.0.2.1.1",
    "summary": "Party Time Texas core customizations for Contacts, CRM, Sales and Projects.",
    "category": "Customizations",
    "author": "Party Time Texas",
    "license": "LGPL-3",
    "depends": ["web", "mail", "contacts", "crm", "project", "sale", "sale_crm", "sale_project", "account", "analytic", "portal", "purchase"],
    "data": [
        # Security (load in correct order per Odoo guidelines)
        # 1. Groups XML - must load first as they may be referenced by other security files
        "security/ptt_business_core_groups.xml",
        # 2. Access rights CSV - references models that must exist
        "security/ir.model.access.csv",
        # 3. Record rules XML - references models from CSV and groups from groups XML
        "security/ptt_project_vendor_assignment_security.xml",
        "security/ptt_vendor_document_security.xml",
        # Legacy security file (kept for backward compatibility, content moved to ptt_business_core_groups.xml)
        "security/ptt_security.xml",
        # Data files
        "data/cleanup_orphaned_fields.xml",
        # CRM stages managed directly in database via SQL - XML files removed to prevent conflicts
        # Stages: Intake, Qualification, Approval, Proposal Sent, Contract Sent, Booked, Closed/Won, Lost
        "data/crm_tags.xml",
        "data/crm_lost_reasons.xml",
        "data/mail_activity_type.xml",
        "data/task_types.xml",
        # Project stages removed - use Odoo defaults to avoid duplicates
        # "data/project_stages.xml",
        "data/sale_order_templates.xml",
        "data/ir_cron.xml",
        # Views - Vendor configuration views FIRST (actions needed by other views)
        "views/ptt_document_type_view.xml",
        "views/ptt_vendor_document_view.xml",
        "views/ptt_vendor_service_tag_view.xml",
        # Views - Main views (may reference vendor actions above)
        "views/ptt_project_vendor_assignment_view.xml",
        "views/ptt_res_partner_view.xml",
        "views/ptt_crm_lead_view.xml",
        "views/ptt_project_project_view.xml",
        "views/ptt_project_task_view.xml",
        # Vendor Views
        "views/ptt_vendor_list_view.xml",
        # Vendor Configuration Menus (load after actions are defined)
        "views/ptt_vendor_config_menus.xml",
        # Vendor Configuration Seed Data (load after views)
        "data/ptt_document_type_data.xml",
        "data/ptt_vendor_service_tag_data.xml",
    ],
    # Demo data disabled - was causing test failures on Odoo.sh
    # "demo": [
    #     "data/demo_data.xml",
    # ],
    "installable": True,
    "application": False,
    "pre_init_hook": "pre_init_hook",
    "post_init_hook": "post_init_hook",
}

