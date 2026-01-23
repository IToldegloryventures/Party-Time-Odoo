# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

from odoo.addons.ptt_business_core.constants import SERVICE_TYPES, CONTACT_METHODS


class ResPartner(models.Model):
    """Partner extensions for Party Time Texas.
    
    Vendor identification uses native Odoo fields:
    - supplier_rank > 0 indicates a vendor
    - customer_rank > 0 indicates a customer
    """
    _inherit = "res.partner"

    # === VENDOR/CLIENT TOGGLES ===
    # These provide Boolean access to the native rank fields
    # NOT stored - computed on-the-fly from supplier_rank
    ptt_is_vendor = fields.Boolean(
        string="Is Vendor",
        compute="_compute_ptt_is_vendor",
        inverse="_inverse_ptt_is_vendor",
        help="Toggle to mark this contact as a vendor (sets supplier_rank = 1)",
    )

    @api.depends("supplier_rank")
    def _compute_ptt_is_vendor(self):
        for partner in self:
            partner.ptt_is_vendor = partner.supplier_rank > 0

    def _inverse_ptt_is_vendor(self):
        for partner in self:
            if partner.ptt_is_vendor and partner.supplier_rank == 0:
                partner.supplier_rank = 1
            elif not partner.ptt_is_vendor and partner.supplier_rank > 0:
                partner.supplier_rank = 0

    # ==========================================================================
    # VENDOR SERVICES - Direct link to actual Odoo service products
    # ==========================================================================
    # Links directly to product.template (services) so when a service is added
    # to a sale order line, we can instantly find vendors who provide it.
    # Auto-updates when you add/change services in Sales > Products.
    ptt_vendor_service_ids = fields.Many2many(
        "product.template",
        "ptt_vendor_service_product_rel",
        "partner_id",
        "product_tmpl_id",
        string="Services Provided",
        domain="[('type', '=', 'service'), ('sale_ok', '=', True)]",
        help="Actual service products this vendor provides. "
             "Select from Sales > Products > Services.",
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
    
    # Client Classification (see customer_rank for client toggle)
    ptt_client_type = fields.Selection(
        [
            ("individual", "Individual"),
            ("business", "Business"),
            ("nonprofit", "Non-Profit"),
            ("government", "Government"),
        ],
        string="Client Type",
    )

    ptt_opportunity_count = fields.Integer(
        string="PTT Opportunities",
        compute="_compute_ptt_opportunity_count",
    )
    
    # Preferred contact method - persisted on Contact record
    # NOTE: CRM Lead has its OWN ptt_preferred_contact field (not related).
    # Sync behavior: Lead value copies to Partner on conversion/link.
    # This allows recording contact preference during lead intake (before partner exists).
    ptt_preferred_contact = fields.Selection(
        selection=CONTACT_METHODS,
        string="Preferred Contact Method",
        help="Client's preferred method of communication. Syncs from CRM Lead when converted.",
    )

    def _compute_ptt_opportunity_count(self):
        """Count related opportunities for client contacts."""
        lead_model = self.env["crm.lead"]
        for partner in self:
            if partner.customer_rank <= 0:
                partner.ptt_opportunity_count = 0
                continue
            partner.ptt_opportunity_count = lead_model.search_count([
                ("partner_id", "child_of", partner.id),
                ("type", "=", "opportunity"),
            ])

    def action_view_ptt_opportunities(self):
        """Open related opportunities for this contact."""
        self.ensure_one()
        action = self.env.ref("crm.crm_lead_action_pipeline").read()[0]
        action["domain"] = [
            ("partner_id", "child_of", self.id),
            ("type", "=", "opportunity"),
        ]
        action["context"] = {
            **self.env.context,
            "default_partner_id": self.id,
            "default_type": "opportunity",
        }
        action["name"] = _("Opportunities")
        return action

    # ==========================================================================
    # VENDOR LOOKUP HELPERS - Find vendors by service product
    # ==========================================================================
    @api.model
    def get_vendors_for_product(self, product):
        """Find all active vendors who provide a specific service product.
        
        Use this when a service is on a sale order line to find available vendors.
        
        Args:
            product: product.product or product.template record
            
        Returns:
            recordset of res.partner (active vendors) who offer this service
        """
        if not product:
            return self.browse()
        
        # Get product template ID
        if product._name == 'product.product':
            tmpl_id = product.product_tmpl_id.id
        else:
            tmpl_id = product.id
        
        return self.search([
            ('ptt_vendor_service_ids', 'in', tmpl_id),
            ('supplier_rank', '>', 0),
        ])

    @api.model
    def get_active_vendors_for_product(self, product):
        """Find active vendors (status=active) who provide a service.
        
        Args:
            product: product.product or product.template record
            
        Returns:
            recordset of res.partner with ptt_vendor_status='active'
        """
        vendors = self.get_vendors_for_product(product)
        # Filter by active status if the field exists (from ptt_vendor_management)
        if 'ptt_vendor_status' in self._fields:
            return vendors.filtered(lambda v: v.ptt_vendor_status == 'active')
        return vendors


