{
    "name": "PTT Business Core",
    "version": "19.0.6.0.0",  # DJ Flagship Config - Hourly pricing + variant config (Jan 2026)
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
        # Legacy security file (kept for backward compatibility, content moved to ptt_business_core_groups.xml)
        "security/ptt_security.xml",
        # Data files
        "data/cleanup_orphaned_fields.xml",
        # Product Categories & Attributes (must load before products)
        # Reference: QuickBooks Chart of Accounts alignment
        "data/product_categories.xml",
        "data/product_attributes.xml",
        # Project Template (must load before products_services.xml because Event Kickoff references it)
        # Uses Odoo native service_tracking + project_template_id for auto-project creation
        "data/project_template.xml",
        # Products (load order: entertainment with variants first, then services, rentals, addons, adjustments)
        "data/products_entertainment.xml",
        # DJ Variant Pricing (must load after entertainment to reference attribute lines)
        "data/dj_variant_pricing.xml",
        # DJ Variant Data (server action to configure variant-specific fields)
        "data/dj_variant_data.xml",
        # DJ Product Cleanup (fixes wrong attribute links)
        "data/cleanup_dj_product.xml",
        # Unarchive Products (reactivates archived products)
        "data/unarchive_products.xml",
        # Fix DJ Prices (forces correct $300 base price)
        "data/fix_dj_prices.xml",
        "data/products_services.xml",
        "data/products_rentals.xml",
        "data/products_addons.xml",
        "data/products_adjustments.xml",
        # CRM stages managed directly in database via SQL - XML files removed to prevent conflicts
        # Stages: Intake, Qualification, Approval, Proposal Sent, Contract Sent, Booked, Closed/Won, Lost
        "data/crm_tags.xml",
        "data/crm_lost_reasons.xml",
        "data/mail_activity_type.xml",
        "data/task_types.xml",
        # Project stages for PTT events (required for stage_id field in views)
        "data/project_stages.xml",
        "data/sale_order_templates.xml",
        "data/ir_cron.xml",
        # Views
        "views/ptt_project_vendor_assignment_view.xml",
        "views/ptt_crm_lead_view.xml",
        # DELETED: ptt_project_project_view.xml - broken Enterprise conflicts
        # DELETED: ptt_project_task_view.xml - empty/disabled
        "views/sale_order_views.xml",  # Price Per Person + Event Details on quotes
        "views/ptt_variant_pricing_config_views.xml",  # Variant Pricing Configuration Wizard (defines action + menu)
    ],
    # Demo data disabled - was causing test failures on Odoo.sh
    # "demo": [
    #     "data/demo_data.xml",
    # ],
    "assets": {
        "web.assets_backend": [
            "ptt_business_core/static/src/scss/crm_lead_notes.scss",
        ],
    },
    "installable": True,
    "application": False,
    "pre_init_hook": "pre_init_hook",
    "post_init_hook": "post_init_hook",
}

