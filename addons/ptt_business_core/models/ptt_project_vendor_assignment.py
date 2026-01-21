# -*- coding: utf-8 -*-
from odoo import models, fields, api

from odoo.addons.ptt_business_core.constants import SERVICE_TYPES, VENDOR_ASSIGNMENT_STATUS


class PttProjectVendorAssignment(models.Model):
    """Actual vendor assignments and costs for projects - execution stage."""
    _name = "ptt.project.vendor.assignment"
    _description = "Project Vendor Assignment"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "service_type, id"

    _positive_estimated_cost = models.Constraint(
        'CHECK (estimated_cost >= 0)',
        'Estimated cost cannot be negative.',
    )
    _positive_actual_cost = models.Constraint(
        'CHECK (actual_cost >= 0)',
        'Actual cost cannot be negative.',
    )

    project_id = fields.Many2one(
        "project.project",
        string="Project",
        required=True,
        ondelete="cascade",
        index=True,
    )
    service_type = fields.Selection(
        selection=SERVICE_TYPES,
        string="Service Type",
        required=True,
        tracking=True,
    )
    vendor_id = fields.Many2one(
        "res.partner",
        string="Vendor",
        domain="[('supplier_rank', '>', 0)]",
        index=True,
        help="Actual vendor assigned for this service",
        tracking=True,
    )
    vendor_name = fields.Char(
        string="Vendor Name",
        compute="_compute_vendor_name",
        store=True,
    )
    vendor_contact = fields.Char(string="Contact Person")
    vendor_phone = fields.Char(
        string="Phone",
        related="vendor_id.phone",
        readonly=True,
    )
    vendor_email = fields.Char(
        string="Email",
        related="vendor_id.email",
        readonly=True,
    )
    
    # Cost tracking
    estimated_cost = fields.Monetary(
        string="Estimated Cost",
        currency_field="currency_id",
        help="Original estimated cost from CRM",
    )
    actual_cost = fields.Monetary(
        string="Actual Cost",
        currency_field="currency_id",
        help="Actual cost we pay to this vendor",
        tracking=True,
    )
    cost_variance = fields.Monetary(
        string="Cost Variance",
        compute="_compute_cost_variance",
        store=True,
        currency_field="currency_id",
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        related="project_id.company_id.currency_id",
        readonly=True,
    )
    
    # Status and dates
    status = fields.Selection(
        selection=VENDOR_ASSIGNMENT_STATUS,
        string="Status",
        default="pending",
        tracking=True,
    )
    contract_date = fields.Date(string="Contract Date")
    service_date = fields.Date(string="Service Date")
    
    # Notes
    description = fields.Text(string="Service Description")
    notes = fields.Text(string="Notes")

    @api.depends("vendor_id", "vendor_id.name")
    def _compute_vendor_name(self):
        """Compute stored vendor name for search and display.
        
        Denormalizes vendor name for faster list views and searching.
        """
        for record in self:
            record.vendor_name = record.vendor_id.name if record.vendor_id else ""

    @api.depends("estimated_cost", "actual_cost")
    def _compute_cost_variance(self):
        """Compute cost variance between actual and estimated.
        
        Returns:
            Positive value = over budget
            Negative value = under budget
        """
        for record in self:
            record.cost_variance = (record.actual_cost or 0) - (record.estimated_cost or 0)

    @api.onchange("vendor_id")
    def _onchange_vendor_id(self):
        """Auto-populate vendor contact name when vendor is selected."""
        if self.vendor_id:
            self.vendor_contact = self.vendor_id.name

    def action_open_form(self):
        """Open the assignment form view"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Vendor Assignment',
            'res_model': 'ptt.project.vendor.assignment',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }

