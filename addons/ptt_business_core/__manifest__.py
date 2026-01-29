{
    'name': 'PTT Business Core',
    'version': '19.0.4.9.0',
    'summary': 'Party Time Texas core business models for event management.',
    'description': """
Party Time Texas Business Core Module
=====================================

Core module that defines the foundational models for PTT event management:
- Partner extensions (vendor marking)
- CRM Lead extensions (event details, service requirements)
- CRM Stage automation (auto-advance on quote/confirm)
- Project extensions (event tracking, vendor assignments)
- Vendor estimate and assignment models
- Sale order line minimum hours validation
- Project templates with 9 standard event tasks (Corporate, Wedding, Social)

NOTE: Products, attributes, categories, and variants are managed NATIVELY
by the accounting team in Odoo - NOT via this module's code.

All custom fields use the ptt_* prefix. No Studio (x_studio_*) fields are used
or required. Legacy Studio fields have been fully migrated and removed.

This module has NO dependencies on other PTT modules.
Other PTT modules depend on this one.
    """,
    'category': 'Customizations',
    'author': 'Party Time Texas',
    'license': 'LGPL-3',
    'depends': [
        'contacts',
        'crm',
        'project',
        'purchase',
        'sale_crm',
        'sale_project',
        'sale_management',
        'product',
        'uom',
        'mail',
    ],
    'data': [
        # Security
        'security/ptt_business_core_groups.xml',
        'security/ir.model.access.csv',
        'security/ptt_project_vendor_assignment_security.xml',
        # Data
        'data/sequences.xml',
        'data/vendor_service_types.xml',
        'data/mail_activity_type.xml',
        'data/crm_stages.xml',
        'data/crm_tags.xml',
        'data/crm_lost_reasons.xml',
        'data/email_templates.xml',
        'data/cron_jobs.xml',
        'data/project_template.xml',
        'data/products_administrative.xml',
        # Views
        'views/res_partner_views.xml',
        'views/crm_lead_views.xml',
        'views/crm_vendor_estimate_views.xml',
        'views/project_vendor_assignment_views.xml',
        'views/project_project_views.xml',
        'views/project_task_views.xml',
        'views/product_views.xml',
        'views/purchase_order_views.xml',
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
