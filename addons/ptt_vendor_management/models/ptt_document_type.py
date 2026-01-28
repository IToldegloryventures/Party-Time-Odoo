# -*- coding: utf-8 -*-
from odoo import models, fields


class PttDocumentType(models.Model):
    """Document types that vendors must provide (COI, W9, etc.)"""
    _name = "ptt.document.type"
    _description = "Vendor Document Type"
    _order = "sequence, name"

    name = fields.Char(
        string="Document Name",
        required=True,
        help="e.g., Certificate of Insurance, W-9 Form",
    )
    
    code = fields.Char(
        string="Code",
        required=True,
        help="e.g., coi, w9, background_check",
    )
    
    description = fields.Text(
        string="Description",
        help="Explanation of what this document is and why it's needed",
    )
    
    required = fields.Boolean(
        string="Required",
        default=False,
        help="If checked, vendors cannot be activated without this document",
    )
    
    has_expiry = fields.Boolean(
        string="Has Expiry Date",
        default=True,
        help="If checked, document must have an expiry date",
    )
    
    expiry_warning_days = fields.Integer(
        string="Warning Days",
        default=30,
        help="Days before expiry to send warning notification",
    )
    
    sequence = fields.Integer(
        default=10,
        help="Display order",
    )
    
    active = fields.Boolean(
        default=True,
        help="If unchecked, this document type will be hidden",
    )
