# -*- coding: utf-8 -*-
"""
RFQ Done Wizard

Wizard to select the winning vendor when closing an RFQ.
"""
from odoo import fields, models, _


class PTTRFQDoneWizard(models.TransientModel):
    """Wizard to select winning vendor for an RFQ."""
    
    _name = "ptt.rfq.done.wizard"
    _description = "RFQ Done Wizard"
    
    rfq_id = fields.Many2one(
        "ptt.vendor.rfq",
        string="RFQ",
        required=True,
    )
    
    quote_ids = fields.Many2many(
        "ptt.vendor.quote.history",
        string="Quotes",
    )
    
    selected_quote_id = fields.Many2one(
        "ptt.vendor.quote.history",
        string="Selected Quote",
        required=True,
        help="Select the winning vendor quote",
    )
    
    def action_confirm(self):
        """Confirm the selected vendor as the winner."""
        self.ensure_one()
        
        if not self.selected_quote_id:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("No Quote Selected"),
                    "message": _("Please select a winning quote."),
                    "type": "warning",
                    "sticky": False,
                },
            }
        
        # Mark quote as selected
        self.selected_quote_id.is_selected = True
        
        # Update RFQ
        self.rfq_id.write({
            "approved_vendor_id": self.selected_quote_id.vendor_id.id,
            "state": "done",
        })
        
        # Post message
        self.rfq_id.message_post(
            body=_("RFQ closed. Selected vendor: %s with quote of %s %s") % (
                self.selected_quote_id.vendor_id.name,
                self.selected_quote_id.quoted_price,
                self.rfq_id.currency_id.symbol,
            ),
        )
        
        return {"type": "ir.actions.act_window_close"}
