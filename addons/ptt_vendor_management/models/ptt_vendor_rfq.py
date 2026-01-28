# -*- coding: utf-8 -*-
"""
PTT Vendor RFQ (Request for Quote) System

This module allows sending quote requests to multiple vendors,
collecting their pricing responses, and selecting a winner.

Reference: https://www.odoo.com/documentation/19.0/developer/tutorials/server_framework_101/
"""
from odoo import api, fields, models, _


class PTTVendorRFQ(models.Model):
    """Vendor RFQ (Request for Quote) model.
    
    Allows sending quote requests to vendors for products/services,
    collecting their responses, and selecting the best vendor.
    """
    _name = "ptt.vendor.rfq"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Vendor RFQ"
    _order = "create_date desc"
    
    # === IDENTIFICATION ===
    name = fields.Char(
        string="RFQ Reference",
        required=True,
        index=True,
        copy=False,
        default=lambda self: _("New"),
        help="Unique reference for this RFQ",
    )
    
    # === PROJECT/EVENT LINK ===
    project_id = fields.Many2one(
        "project.project",
        string="Event/Project",
        domain="[('is_template', '=', False)]",
        help="The event or project this RFQ is for (excludes templates)",
        tracking=True,
    )
    
    # Related fields for easy display
    event_date = fields.Date(
        string="Event Date",
        related="project_id.ptt_event_date",
        store=True,
        readonly=True,
    )
    
    customer_id = fields.Many2one(
        "res.partner",
        string="Customer",
        related="project_id.partner_id",
        store=True,
        readonly=True,
    )
    
    # === PRODUCT/SERVICE INFO ===
    product_id = fields.Many2one(
        "product.product",
        string="Product/Service",
        help="The product or service being quoted",
    )
    
    description = fields.Text(
        string="Description",
        help="Detailed description of what you need quoted",
    )
    
    quantity = fields.Float(
        string="Quantity",
        default=1.0,
        help="Quantity required",
    )
    
    uom_id = fields.Many2one(
        "uom.uom",
        string="Unit of Measure",
        help="Unit of measure for the quantity",
    )
    
    # === PRICING ===
    estimated_quote = fields.Monetary(
        string="Estimated Quote",
        currency_field="currency_id",
        help="Your estimated quote price for comparison",
    )
    
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        required=True,
        default=lambda self: self.env.company.currency_id,
    )
    
    # === DATES ===
    quote_date = fields.Date(
        string="Quote Date",
        default=fields.Date.today,
        help="Date the RFQ was created",
    )
    
    closing_date = fields.Date(
        string="Closing Date",
        help="Deadline for vendors to submit quotes",
    )
    
    estimated_delivery_date = fields.Date(
        string="Requested Delivery Date",
        help="When you need the product/service delivered",
    )
    
    # === VENDORS ===
    vendor_ids = fields.Many2many(
        "res.partner",
        "ptt_vendor_rfq_partner_rel",
        "rfq_id",
        "partner_id",
        string="Invited Vendors",
        domain="[('supplier_rank', '>', 0)]",
        help="Vendors invited to quote on this RFQ",
    )
    
    # === QUOTE RESPONSES ===
    quote_history_ids = fields.One2many(
        "ptt.vendor.quote.history",
        "rfq_id",
        string="Vendor Quotes",
        help="Quote responses from vendors",
    )
    
    # === RESULT ===
    approved_vendor_id = fields.Many2one(
        "res.partner",
        string="Approved Vendor",
        help="The vendor selected for this RFQ",
    )
    
    order_id = fields.Many2one(
        "purchase.order",
        string="Purchase Order",
        help="Purchase order created from this RFQ",
    )
    
    # === ADDITIONAL INFO ===
    notes = fields.Html(
        string="Notes",
        help="Additional notes or requirements",
    )
    
    user_id = fields.Many2one(
        "res.users",
        string="Responsible",
        default=lambda self: self.env.user,
        help="Person responsible for this RFQ",
    )
    
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
    )
    
    # === STATE ===
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("pending", "Pending"),
            ("in_progress", "In Progress"),
            ("done", "Done"),
            ("order", "Purchase Order"),
            ("cancel", "Cancelled"),
        ],
        string="Status",
        default="draft",
        tracking=True,
        help="Current state of the RFQ",
    )
    
    # === COMPUTED FIELDS ===
    quote_count = fields.Integer(
        string="Quote Count",
        compute="_compute_quote_count",
    )
    
    lowest_quote = fields.Monetary(
        string="Lowest Quote",
        compute="_compute_quote_stats",
        currency_field="currency_id",
    )
    
    @api.depends("quote_history_ids")
    def _compute_quote_count(self):
        for record in self:
            record.quote_count = len(record.quote_history_ids)
    
    @api.depends("quote_history_ids", "quote_history_ids.quoted_price")
    def _compute_quote_stats(self):
        for record in self:
            prices = record.quote_history_ids.filtered(
                lambda q: q.quoted_price > 0
            ).mapped("quoted_price")
            record.lowest_quote = min(prices) if prices else 0.0
    
    # === CRUD OVERRIDES ===
    @api.model_create_multi
    def create(self, vals_list):
        """Auto-generate sequence number on create."""
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code("ptt.vendor.rfq") or _("New")
        return super().create(vals_list)
    
    # === ACTIONS ===
    def action_open_send_wizard(self):
        """Open wizard to select vendors and send RFQ invitations."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Send RFQ to Vendors"),
            "res_model": "ptt.rfq.send.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_rfq_id": self.id},
        }
    
    def action_send_invitations(self):
        """Send invitation emails to all selected vendors."""
        self.ensure_one()
        
        if not self.vendor_ids:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("No Vendors Selected"),
                    "message": _("Please select vendors to invite."),
                    "type": "warning",
                    "sticky": False,
                },
            }
        
        template = self.env.ref(
            "ptt_vendor_management.email_template_vendor_rfq_invitation",
            raise_if_not_found=False
        )
        
        if template:
            for vendor in self.vendor_ids:
                template.send_mail(
                    self.id,
                    force_send=True,
                    email_values={"email_to": vendor.email},
                )
        
        self.state = "in_progress"
        self.message_post(
            body=_("RFQ invitation sent to %s vendors.") % len(self.vendor_ids),
        )
        
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Invitations Sent"),
                "message": _("RFQ invitations sent to %s vendors.") % len(self.vendor_ids),
                "type": "success",
                "sticky": False,
            },
        }
    
    def action_set_pending(self):
        """Set RFQ to pending state."""
        self.state = "pending"
    
    def action_cancel(self):
        """Cancel the RFQ."""
        self.state = "cancel"
    
    def action_mark_done(self):
        """Open wizard to select winning vendor."""
        self.ensure_one()
        
        if not self.quote_history_ids:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("No Quotes Received"),
                    "message": _("No vendor quotes have been received yet."),
                    "type": "warning",
                    "sticky": False,
                },
            }
        
        return {
            "type": "ir.actions.act_window",
            "name": _("Select Winning Vendor"),
            "res_model": "ptt.rfq.done.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_rfq_id": self.id,
                "default_quote_ids": [(6, 0, self.quote_history_ids.ids)],
            },
        }
    
    def action_create_purchase_order(self):
        """Create a purchase order from the approved quote."""
        self.ensure_one()
        
        if not self.approved_vendor_id:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("No Approved Vendor"),
                    "message": _("Please select an approved vendor first."),
                    "type": "warning",
                    "sticky": False,
                },
            }
        
        # Get the approved vendor's quote
        approved_quote = self.quote_history_ids.filtered(
            lambda q: q.vendor_id == self.approved_vendor_id
        )
        
        if not approved_quote:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("No Quote Found"),
                    "message": _("No quote found from the approved vendor."),
                    "type": "warning",
                    "sticky": False,
                },
            }
        
        approved_quote = approved_quote[0]
        
        # Create purchase order
        po_vals = {
            "partner_id": self.approved_vendor_id.id,
        }
        if self.project_id:
            po_vals["ptt_project_id"] = self.project_id.id
        
        if self.product_id:
            po_vals["order_line"] = [(0, 0, {
                "name": self.product_id.name,
                "product_id": self.product_id.id,
                "product_qty": self.quantity,
                "product_uom": self.product_id.uom_po_id.id or self.uom_id.id,
                "price_unit": approved_quote.quoted_price,
                "date_planned": approved_quote.estimate_date or fields.Date.today(),
            })]
        
        order = self.env["purchase.order"].create(po_vals)
        
        self.write({
            "state": "order",
            "order_id": order.id,
        })
        
        return {
            "type": "ir.actions.act_window",
            "res_model": "purchase.order",
            "res_id": order.id,
            "view_mode": "form",
            "target": "current",
        }
    
    def action_view_purchase_order(self):
        """View the linked purchase order."""
        self.ensure_one()
        if self.order_id:
            return {
                "type": "ir.actions.act_window",
                "res_model": "purchase.order",
                "res_id": self.order_id.id,
                "view_mode": "form",
                "target": "current",
            }
    
    # === CRON METHODS ===
    @api.model
    def cron_auto_close_rfqs(self):
        """Automatically close RFQs past their closing date.
        
        Called by scheduled action. Selects the lowest-priced vendor
        that submitted a quote.
        """
        today = fields.Date.today()
        
        rfqs_to_close = self.search([
            ("state", "=", "in_progress"),
            ("closing_date", "<=", today),
            ("quote_history_ids", "!=", False),
        ])
        
        for rfq in rfqs_to_close:
            # Find the lowest quote
            quotes = rfq.quote_history_ids.filtered(lambda q: q.quoted_price > 0)
            if quotes:
                best_quote = min(quotes, key=lambda q: q.quoted_price)
                rfq.write({
                    "approved_vendor_id": best_quote.vendor_id.id,
                    "state": "done",
                })
                rfq.message_post(
                    body=_("RFQ auto-closed. Lowest quote from %s: %s %s") % (
                        best_quote.vendor_id.name,
                        best_quote.quoted_price,
                        rfq.currency_id.symbol,
                    ),
                )
