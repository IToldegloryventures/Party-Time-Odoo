{
    "name": "PTT Event Management",
    "version": "19.0.1.0.0",
    "category": "Sales",
    "summary": "Event management fields for Party Time Texas",
    "description": """
        Party Time Texas Event Management Module
        =========================================
        
        Extends CRM, Sales, and Accounting with comprehensive event planning fields:
        - Event Overview (type, date, time, guest count, location)
        - Services Requested linked to actual Products  
        - Auto-populate quote lines from selected services
        - Guest Count flows through entire sales process
        - Price Per Person computed on quotes and invoices
        - Time fields with proper dropdown selection
    """,
    "author": "Party Time Texas",
    "license": "LGPL-3",
    "depends": [
        "base",
        "crm",
        "sale",
        "sale_crm",
        "sale_management",
        "account",
        "product",
        "ptt_business_core",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/product_data.xml",
        "views/crm_lead_views.xml",
        "views/sale_order_views.xml",
        "views/account_move_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
