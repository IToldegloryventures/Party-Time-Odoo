# -*- coding: utf-8 -*-
{
    'name': 'Party Time Event Management',

    'summary': """
        Event Management system for Party Time with account.move and CRM integration.
        Tracks event details on invoices and automatically computes pricing metrics.""",

    'description': """
        Party Time Event Management Module
        ===================================

        This module extends Odoo's accounting and CRM modules to track event-related
        information on invoices and sale orders. It provides comprehensive event
        management capabilities with automatic field computation.

        Features:
        ---------
        * Event Classification: Type, name, date, and time tracking
        * Guest Management: Guest count and price per person calculation
        * Venue Management: Location type and venue booking information
        * Automatic Synchronization: Event fields automatically sync from sale orders
        * CRM Integration: Extended CRM leads with event tracking
        * Invoice Enhancement: Event details appear on customer invoices
        * Computed Fields: Automatic calculations for pricing and duration

        Models Extended:
        ----------------
        * account.move: Added event overview and pricing fields
        * crm.lead: Added event classification and details
        * sale.order: Event information integration (prerequisites)

        Dependencies:
        -------
        Requires: base, sale, account, crm modules
    """,

    'author': 'Party Time',
    'website': 'https://www.partytime.example.com',
    'license': 'LGPL-3',
    'category': 'Sales/CRM',
    'version': '19.0.1.0.0',

    'depends': [
        'base',
        'sale',
        'account',
        'crm',
    ],

    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],

    'demo': [
        'demo/demo.xml',
    ],

    'installable': True,
    'application': False,
    'auto_install': False,
}
