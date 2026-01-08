# -*- coding: utf-8 -*-
{
    "name": "PTT Contact Forms",
    "version": "19.0.1.0.2",
    "summary": "Public contact forms that create CRM leads - embeddable in external websites",
    "description": """
        Party Time Texas - Public Contact Forms
        ========================================
        
        Creates public landing pages for:
        - Contact Us form (creates CRM leads)
        - Future: Feedback surveys, event inquiries, etc.
        
        Features:
        - No login required (public access)
        - Creates CRM leads automatically
        - Embeddable via iframe in WordPress/external sites
        - Mobile responsive design
        - CORS enabled for cross-origin requests
        
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
