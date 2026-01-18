{
    "name": "PTT Business Core",
    "version": "19.0.3.1.0",
    "summary": "Party Time Texas core business models for event management.",
    "description": """
Party Time Texas Business Core Module
=====================================

Core module that defines the foundational models for PTT event management:
- Partner extensions (vendor marking)
- CRM Lead extensions (event details, service requirements)
- Project extensions (event tracking, vendor assignments)
- Vendor estimate and assignment models
- Product variants with Event Type × Service Tier attributes
- Per-variant pricing fields (min hours, guest counts, cost guides)
- Sale order line minimum hours validation

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
        "sale_crm",
        "sale_project",
        "sale_management",
        "product",
        "uom",
        "mail",
    ],
    "data": [
        # Security
        "security/ir.model.access.csv",
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
        "data/dj_variant_config.xml",
        # Views
        "views/res_partner_views.xml",
        "views/crm_lead_views.xml",
        "views/crm_vendor_estimate_views.xml",
        "views/project_vendor_assignment_views.xml",
        "views/project_project_views.xml",
        "views/product_views.xml",
        "views/sale_order_views.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
}

