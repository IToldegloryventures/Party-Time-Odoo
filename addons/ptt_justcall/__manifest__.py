# -*- coding: utf-8 -*-
{
    'name': 'PTT JustCall Integration',
    'version': '19.0.1.0.0',
    'category': 'CRM',
    'summary': 'Integrate JustCall VoIP with Odoo CRM for click-to-call, call logging, and SMS',
    'description': """
JustCall Integration for Odoo 19
================================

Features:
---------
* Click-to-Call: Call contacts and leads directly from Odoo
* Call Logging: Automatic call history via webhooks
* SMS Integration: Send SMS from contact/lead records
* Call History: View all calls on partner and lead records
* Recording Access: Link to call recordings from Odoo
* User Mapping: Map JustCall users to Odoo users by email

Configuration:
--------------
1. Go to Settings → JustCall Configuration
2. Enter your API Key and API Secret from JustCall
3. Configure webhook URL in JustCall dashboard
4. Map users if email addresses don't match

Requirements:
-------------
* JustCall account with API access (Team plan or higher)
* Odoo 19.0 or higher
    """,
    'author': 'Party Time Texas',
    'website': 'https://www.odoo.com',
    'depends': [
        'base',
        'sales_team',  # Required for module_category_sales_crm
        'crm',
        'contacts',
        'project',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/ptt_justcall_security.xml',
        'data/ir_config_parameter.xml',
        'views/justcall_config_views.xml',
        'views/justcall_call_views.xml',
        'views/justcall_user_mapping_views.xml',
        'views/res_partner_views.xml',
        'views/crm_lead_views.xml',
        'views/project_project_views.xml',
        'views/justcall_menu.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
