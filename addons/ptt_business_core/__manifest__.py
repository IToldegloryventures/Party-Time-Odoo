{
    "name": "PTT Business Core",
    "version": "19.0.1.2.1",
    "summary": "Party Time Texas core customizations for Contacts, CRM, Sales and Projects.",
    "category": "Customizations",
    "author": "Party Time Texas",
    "license": "LGPL-3",
    "depends": ["web", "contacts", "crm", "project", "sale", "sale_crm", "sale_project", "account", "analytic"],
    "data": [
        # Security (load groups first, then access rules)
        "security/ptt_security.xml",
        "security/ir.model.access.csv",
        # Data files
        "data/cleanup_orphaned_fields.xml",
        "data/crm_stages.xml",
        "data/crm_tags.xml",
        "data/crm_lost_reasons.xml",
        "data/mail_activity_type.xml",
        "data/task_types.xml",
        "data/project_stages.xml",
        "data/sale_order_templates.xml",
        "data/ir_cron.xml",
        # Views
        "views/ptt_crm_vendor_estimate_view.xml",
        "views/ptt_project_vendor_assignment_view.xml",
        "views/ptt_res_partner_view.xml",
        "views/ptt_crm_lead_view.xml",
        "views/ptt_project_project_view.xml",
        "views/ptt_sale_order_view.xml",
    ],
    "demo": [
        "data/demo_data.xml",
    ],
    "installable": True,
    "application": False,
    "pre_init_hook": "pre_init_hook",
}

