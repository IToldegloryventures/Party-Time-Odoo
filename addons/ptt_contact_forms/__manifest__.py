# -*- coding: utf-8 -*-
{
    "name": "PTT Contact Forms",
    "version": "19.0.1.0.4",
    "summary": "Public contact forms with WordPress webhook API for CRM lead creation",
    "description": """
        Party Time Texas - Public Contact Forms
        ========================================
        
        Creates public landing pages for:
        - Contact Us form (creates CRM leads)
        - WordPress Webhook API endpoint
        
        Features:
        - No login required (public access)
        - Creates CRM leads automatically
        - Embeddable via iframe in WordPress/external sites
        - **WordPress Webhook API** at /api/contact-form
        - JSON API with CORS support
        - Mobile responsive design
        
        WordPress Integration:
        - POST JSON to: https://your-odoo.com/api/contact-form
        - Returns: {"success": true, "lead_id": 123}
        - Works with WPForms, Gravity Forms, Contact Form 7, etc.
        
        Based on Odoo Portal architecture per:
        https://www.odoo.com/documentation/19.0/developer/howtos/website_themes/theming.html
    """,
    "category": "Website",
    "author": "Party Time Texas",
    "license": "LGPL-3",
    "depends": ["web", "portal", "crm", "ptt_business_core"],
    "data": [
        "templates/contact_form.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "ptt_contact_forms/static/src/css/contact_form.css",
            "ptt_contact_forms/static/src/js/contact_form.js",
        ],
    },
    "installable": True,
    "application": False,
}
