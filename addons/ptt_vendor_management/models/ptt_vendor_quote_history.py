This file is being deleted as it is no longer needed.
"""
PTT Vendor Quote History

Tracks quote responses from vendors for RFQs.
"""
from odoo import fields, models


class PTTVendorQuoteHistory(models.Model):
    """Vendor Quote History - stores quote responses from vendors."""
    
    _name = "ptt.vendor.quote.history"
    _description = "Vendor Quote History"
    _rec_name = "vendor_id"
    _order = "quoted_price asc"
    
    # === VENDOR ===
    vendor_id = fields.Many2one(
        "res.partner",
        string="Vendor",
        required=True,
        domain="[('supplier_rank', '>', 0)]",
        help="The vendor who submitted this quote",
    )
    
    # === PRICING ===
    quoted_price = fields.Monetary(
        string="Quoted Price",
        currency_field="currency_id",
        required=True,
        help="Price quoted by the vendor",
    )
    
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        required=True,
        default=lambda self: self.env.company.currency_id,
    )
    
    # === DELIVERY ===
    estimate_date = fields.Date(
        string="Estimated Delivery Date",
        help="Vendor's estimated delivery date",
    )
    
    # === RFQ LINK ===
    rfq_id = fields.Many2one(
        "ptt.vendor.rfq",
        string="RFQ",
        required=True,
        ondelete="cascade",
        help="The RFQ this quote is for",
    )
    
    # === ADDITIONAL INFO ===
    note = fields.Text(
        string="Note",
        help="Additional notes from the vendor",
    )
    
    # === TRACKING ===
    submit_date = fields.Datetime(
        string="Submitted",
        default=fields.Datetime.now,
        help="When this quote was submitted",
    )
    
    is_selected = fields.Boolean(
        string="Selected",
        default=False,
        help="Whether this quote was selected as the winner",
    )
