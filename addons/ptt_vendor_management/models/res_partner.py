from odoo import models, fields, api


class ResPartner(models.Model):
    """Extend res.partner for PTT vendor management fields.
    
    This module adds vendor-specific fields and functionality to partners.
    """
    _inherit = "res.partner"

    # === VENDOR TOGGLE ===
    x_is_vendor = fields.Boolean(
        string="Is a Vendor",
        default=False,
        help="Toggle on to mark this contact as a vendor. This will show vendor-specific fields and tabs.",
    )

    # === VENDOR SERVICE TAGS & TIER ===
    x_vendor_service_tag_ids = fields.Many2many(
        "ptt.vendor.service.tag",
        "res_partner_vendor_service_tag_rel",
        "partner_id",
        "tag_id",
        string="Services Provided",
        help="Service categories this vendor provides (DJ, Photography, etc.)",
    )
    
    x_vendor_tier = fields.Selection(
        [
            ("gold", "Gold"),
            ("silver", "Silver"),
            ("bronze", "Bronze"),
        ],
        string="Vendor Tier",
        help="Overall quality tier for this vendor. Used to match with product tiers when assigning vendors to quotes.",
    )
    
    # === VENDOR CONTACT ROLE (for contacts under vendor companies) ===
    x_vendor_contact_role = fields.Char(
        string="Role at Vendor",
        help="This person's role at the vendor company (e.g., Owner, Talent, Accounting)",
    )

    @api.onchange("x_is_vendor")
    def _onchange_x_is_vendor(self):
        """When vendor toggle is switched on, set supplier_rank so Odoo treats this as a vendor."""
        if self.x_is_vendor and self.supplier_rank == 0:
            self.supplier_rank = 1
        elif not self.x_is_vendor and self.supplier_rank > 0:
            # Optionally reset supplier_rank when toggle is off
            self.supplier_rank = 0

    # === VENDOR DOCUMENT RELATION ===
    x_vendor_document_ids = fields.One2many(
        "ptt.vendor.document",
        "vendor_id",
        string="Vendor Documents",
        help="Documents uploaded by or for this vendor",
    )
    
    x_vendor_document_count = fields.Integer(
        string="Vendor Docs",
        compute="_compute_vendor_compliance",
    )
    
    x_vendor_compliance_status = fields.Selection(
        [
            ("compliant", "Compliant"),
            ("missing_required", "Missing Required"),
            ("expired", "Expired Documents"),
            ("expiring_soon", "Expiring Soon"),
        ],
        string="Compliance Status",
        compute="_compute_vendor_compliance",
        store=True,
        help="Vendor document compliance status based on required documents",
    )

    @api.depends("x_is_vendor", "x_vendor_document_ids", "x_vendor_document_ids.status", 
                 "x_vendor_document_ids.document_type_id.required")
    def _compute_vendor_compliance(self):
        """Compute vendor compliance status based on required documents."""
        required_doc_types = self.env["ptt.document.type"].search([("required", "=", True)])
        required_type_ids = set(required_doc_types.ids)
        
        for partner in self:
            partner.x_vendor_document_count = len(partner.x_vendor_document_ids)
            
            # Only compute compliance for vendors (x_is_vendor toggled on)
            if not partner.x_is_vendor:
                partner.x_vendor_compliance_status = False
                continue
            
            # Get this vendor's documents
            vendor_docs = partner.x_vendor_document_ids
            vendor_doc_type_ids = set(vendor_docs.mapped("document_type_id").ids)
            
            # Check for missing required documents
            missing_required = required_type_ids - vendor_doc_type_ids
            if missing_required:
                partner.x_vendor_compliance_status = "missing_required"
                continue
            
            # Check for expired documents (among required types)
            expired_docs = vendor_docs.filtered(
                lambda d: d.document_type_id.required and d.status == "expired"
            )
            if expired_docs:
                partner.x_vendor_compliance_status = "expired"
                continue
            
            # Check for expiring soon documents (among required types)
            expiring_docs = vendor_docs.filtered(
                lambda d: d.document_type_id.required and d.status == "expiring_soon"
            )
            if expiring_docs:
                partner.x_vendor_compliance_status = "expiring_soon"
                continue
            
            # All required documents present and valid
            partner.x_vendor_compliance_status = "compliant"
    
    # === VENDOR NOTES ===
    x_vendor_notes = fields.Text(
        string="Vendor Notes",
        help="Internal notes about this vendor. Visible only to internal users. "
             "This field can be imported via CSV using the column name 'x_vendor_notes'.",
    )
    
    # === LEGACY VENDOR FIELDS (kept for compatibility) ===
    x_vendor_rating = fields.Selection(
        [
            ("1", "1 Star"),
            ("2", "2 Stars"),
            ("3", "3 Stars"),
            ("4", "4 Stars"),
            ("5", "5 Stars"),
        ],
        string="Rating",
        help="Vendor performance rating",
    )
