# -*- coding: utf-8 -*-
from odoo import models, fields

from odoo.addons.ptt_business_core.constants import SERVICE_TYPES


class ResPartner(models.Model):
    """Partner extensions for Party Time Texas."""
    _inherit = "res.partner"

    # Vendor Classification
    ptt_is_vendor = fields.Boolean(
        string="Is PTT Vendor",
        help="Mark this contact as a vendor/service provider for Party Time Texas.",
    )
    ptt_vendor_service_types = fields.Many2many(
        "ptt.vendor.service.type",
        string="Service Types",
        help="Types of services this vendor provides.",
    )
    ptt_vendor_rating = fields.Selection(
        [
            ("1", "1 - Poor"),
            ("2", "2 - Fair"),
            ("3", "3 - Good"),
            ("4", "4 - Very Good"),
            ("5", "5 - Excellent"),
        ],
        string="Vendor Rating",
    )
    ptt_vendor_notes = fields.Text(
        string="Vendor Notes",
        help="Internal notes about this vendor.",
    )
    
    # Client Classification
    ptt_is_client = fields.Boolean(
        string="Is PTT Client",
        help="Mark this contact as a Party Time Texas client.",
    )
    ptt_client_type = fields.Selection(
        [
            ("individual", "Individual"),
            ("business", "Business"),
            ("nonprofit", "Non-Profit"),
            ("government", "Government"),
        ],
        string="Client Type",
    )
    
    # Preferred contact method
    ptt_preferred_contact = fields.Selection(
        [
            ("call", "Phone Call"),
            ("text", "Text Message"),
            ("email", "Email"),
        ],
        string="Preferred Contact Method",
    )


class PttVendorServiceType(models.Model):
    """Vendor service type tags."""
    _name = "ptt.vendor.service.type"
    _description = "Vendor Service Type"
    _order = "sequence, name"

    name = fields.Char(string="Service Type", required=True)
    code = fields.Char(string="Code")
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    color = fields.Integer(string="Color Index")


