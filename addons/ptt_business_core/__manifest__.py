{
    "name": "PTT Business Core",
    "version": "19.0.4.3.1",
    "summary": "Party Time Texas core business models for event management.",
    "description": """
Party Time Texas Business Core Module
=====================================

Core module that defines the foundational models for PTT event management:
- Partner extensions (vendor marking)
- CRM Lead extensions (event details, service requirements)
- CRM Stage automation (auto-advance on quote/confirm)
- Project extensions (event tracking, vendor assignments)
- Vendor estimate and assignment models
- Product variants with Event Type × Service Tier attributes
- Per-variant pricing fields (min hours, guest counts, cost guides)
- Sale order line minimum hours validation
- Project templates with 9 standard event tasks

IMPORTANT: This module uses existing Studio fields (x_studio_*) directly:
- x_studio_event_name, x_studio_event_date
- x_studio_venue_name, x_studio_venue_address

This module has NO dependencies on other PTT modules.
Other PTT modules depend on this one.
    """,
    "category": "Customizations",
    "author": "Party Time Texas",
    "license": "LGPL-3",
    "depends": [
        "contacts",
        "crm",
        "project",
        "purchase",
        "sale_crm",
        "sale_project",
        "sale_management",
        "product",
        "uom",
        "mail",
    ],
    "data": [
        # Security - Groups first (referenced by other security files)
        "security/ptt_business_core_groups.xml",
        "security/ir.model.access.csv",
        "security/ptt_project_vendor_assignment_security.xml",
        # Data - Sequences (load first for ID generation)
        "data/sequences.xml",
        # Data - Task Types (load before project template)
        "data/task_types.xml",
        # Data - Project Template (load before products)
        "data/project_template.xml",
        # Data - Activity Types
        "data/mail_activity_type.xml",
        # Data - CRM Configuration
        "data/crm_stages.xml",
        "data/crm_tags.xml",
        "data/crm_lost_reasons.xml",
        # Data - Email Templates (must load before cron jobs)
        "data/email_templates.xml",
        # Data - Scheduled Actions
        "data/cron_jobs.xml",
        # Data - Product Configuration (load order matters)
        "data/product_attributes.xml",
        "data/product_categories.xml",
        "data/products_entertainment.xml",
        "data/products_services.xml",
        "data/products_rentals.xml",
        "data/products_adjustments.xml",
        "data/products_administrative.xml",
        "data/dj_variant_config.xml",
        # Views
        "views/res_partner_views.xml",
        "views/crm_lead_views.xml",
        "views/crm_vendor_estimate_views.xml",
        "views/project_vendor_assignment_views.xml",
        "views/project_project_views.xml",
        "views/project_task_views.xml",
        "views/product_views.xml",
        "views/purchase_order_views.xml",
        "views/sale_order_views.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
}
