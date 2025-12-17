{
    "name": "PTT Business Core",
    "version": "19.0.1.0.4",
    "summary": "Party Time Texas core customizations for Contacts, CRM and Projects.",
    "category": "Hidden/Custom",
    "author": "Party Time Texas",
    "license": "LGPL-3",
    "depends": ["contacts", "crm", "project", "sale_crm"],
    "data": [
        "security/ir.model.access.csv",
        "data/cleanup_orphaned_fields.xml",
        "views/ptt_crm_vendor_estimate_view.xml",
        "views/ptt_project_vendor_assignment_view.xml",
        "views/ptt_res_partner_view.xml",
        "views/ptt_crm_lead_view.xml",
        "views/ptt_project_project_view.xml",
    ],
    "installable": True,
    "application": False,
    "pre_init_hook": "pre_init_hook",
    "post_init_hook": "post_init_hook",
}

