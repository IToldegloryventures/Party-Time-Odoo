# -*- coding: utf-8 -*-
from odoo import models, fields

from odoo.addons.ptt_business_core.constants import SERVICE_TYPES


class PttCrmVendorEstimate(models.Model):
    """Estimated vendor costs for CRM opportunities - planning stage."""
    _name = "ptt.crm.vendor.estimate"
    _description = "CRM Lead Vendor Cost Estimate"
    _order = "service_type, id"

    # =========================================================================
    # SQL CONSTRAINTS
    # =========================================================================
    _sql_constraints = [
        ('positive_estimated_cost', 'CHECK (estimated_cost >= 0)',
         'Estimated cost cannot be negative.'),
    ]

    crm_lead_id = fields.Many2one(
        "crm.lead",
        string="Opportunity",
        required=True,
        ondelete="cascade",
        index=True,
    )
    service_type = fields.Selection(
        selection=SERVICE_TYPES,
        string="Service Type",
        required=True,
    )
    vendor_name = fields.Char(
        string="Vendor Name (Estimated)",
        help="Name of vendor we expect to use"
    )
    estimated_cost = fields.Monetary(
        string="Estimated Cost",
        currency_field="currency_id",
        required=True,
        help="Estimated cost we will pay to this vendor",
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        related="crm_lead_id.company_currency",
        store=True,
        readonly=True,
    )
    notes = fields.Text(string="Notes")

