from odoo import models, fields, api


class ResPartner(models.Model):
    """Extend res.partner for PTT vendor management fields.
    
    This module adds vendor-specific fields and functionality to partners.
    
    VENDOR IDENTIFICATION:
    - Uses native Odoo supplier_rank field (supplier_rank > 0 = vendor)
    - No custom x_is_vendor field needed - this is Odoo best practice
    - Set supplier_rank = 1 when creating a vendor
    
    FIELD NAMING:
    - All custom fields use ptt_ prefix (Party Time Texas)
    - This follows Odoo best practice: x_ is reserved for Studio fields
    
    PERFORMANCE:
    - Required document types are cached per-environment to avoid repeated searches
    - Compliance computation only runs for vendors (supplier_rank > 0)
    """
    _inherit = "res.partner"

    # === VENDOR SERVICE TAGS & TIER ===
    ptt_vendor_service_tag_ids = fields.Many2many(
        "ptt.vendor.service.tag",
        "res_partner_vendor_service_tag_rel",
        "partner_id",
        "tag_id",
        string="Services Provided",
        help="Service categories this vendor provides (DJ, Photography, etc.)",
    )
    
    ptt_vendor_tier = fields.Selection(
        [
            ("gold", "Gold"),
            ("silver", "Silver"),
            ("bronze", "Bronze"),
        ],
        string="Vendor Tier",
        help="Overall quality tier for this vendor. Used to match with product tiers when assigning vendors to quotes.",
    )
    
    # === VENDOR CONTACT ROLE (for contacts under vendor companies) ===
    ptt_vendor_contact_role = fields.Char(
        string="Role at Vendor",
        help="This person's role at the vendor company (e.g., Owner, Talent, Accounting)",
    )

    # === VENDOR DOCUMENT RELATION ===
    ptt_vendor_document_ids = fields.One2many(
        "ptt.vendor.document",
        "vendor_id",
        string="Vendor Documents",
        help="Documents uploaded by or for this vendor",
    )
    
    ptt_vendor_document_count = fields.Integer(
        string="Vendor Docs",
        compute="_compute_vendor_document_count",
    )
    
    ptt_vendor_compliance_status = fields.Selection(
        [
            ("compliant", "Compliant"),
            ("missing_required", "Missing Required"),
            ("expired", "Expired Documents"),
            ("expiring_soon", "Expiring Soon"),
        ],
        string="Compliance Status",
        compute="_compute_vendor_compliance_status",
        store=True,
        help="Vendor document compliance status based on required documents",
    )

    @api.depends("ptt_vendor_document_ids")
    def _compute_vendor_document_count(self):
        """Compute document count (non-stored field)."""
        for partner in self:
            partner.ptt_vendor_document_count = len(partner.ptt_vendor_document_ids)

    @api.model
    def _get_required_document_type_ids(self):
        """Get required document type IDs with per-environment caching."""
        cache_key = '_ptt_required_doc_type_ids'
        if not hasattr(self.env, cache_key):
            required_doc_types = self.env["ptt.document.type"].search([
                ("required", "=", True)
            ])
            setattr(self.env, cache_key, set(required_doc_types.ids))
        return getattr(self.env, cache_key)

    @api.depends("supplier_rank", "ptt_vendor_document_ids", "ptt_vendor_document_ids.status", 
                 "ptt_vendor_document_ids.document_type_id.required")
    def _compute_vendor_compliance_status(self):
        """Compute vendor compliance status based on required documents (stored field)."""
        required_type_ids = self._get_required_document_type_ids()
        
        for partner in self:
            if partner.supplier_rank <= 0:
                partner.ptt_vendor_compliance_status = False
                continue
            
            # Get this vendor's documents
            vendor_docs = partner.ptt_vendor_document_ids
            vendor_doc_type_ids = set(vendor_docs.mapped("document_type_id").ids)
            
            # Check for missing required documents
            missing_required = required_type_ids - vendor_doc_type_ids
            if missing_required:
                partner.ptt_vendor_compliance_status = "missing_required"
                continue
            
            # Check for non-compliant documents (among required types)
            non_compliant_docs = vendor_docs.filtered(
                lambda d: d.document_type_id.required and d.status == "non_compliant"
            )
            if non_compliant_docs:
                partner.ptt_vendor_compliance_status = "expired"
                continue
            
            # Check for expiring soon documents (among required types)
            expiring_docs = vendor_docs.filtered(
                lambda d: d.document_type_id.required and d.status == "expiring_soon"
            )
            if expiring_docs:
                partner.ptt_vendor_compliance_status = "expiring_soon"
                continue
            
            # All required documents present and valid
            partner.ptt_vendor_compliance_status = "compliant"
    
    # === VENDOR NOTES ===
    ptt_vendor_notes = fields.Text(
        string="Vendor Notes",
        help="Internal notes about this vendor. Visible only to internal users.",
    )
    
    @api.model_create_multi
    def create(self, vals_list):
        """Auto-populate standard document lines when creating a vendor."""
        records = super().create(vals_list)
        
        # Auto-populate document lines for new vendors
        for record in records:
            if record.supplier_rank > 0:
                record._populate_vendor_document_lines()
        
        return records
    
    def write(self, vals):
        """Auto-populate document lines when partner becomes a vendor."""
        # Check if becoming a vendor (supplier_rank going from 0 to > 0)
        becoming_vendor = 'supplier_rank' in vals and vals['supplier_rank'] > 0
        was_vendor = self.filtered(lambda p: p.supplier_rank > 0)
        
        result = super().write(vals)
        
        if becoming_vendor:
            new_vendors = self.filtered(lambda p: p.supplier_rank > 0 and p not in was_vendor)
            for vendor in new_vendors:
                vendor._populate_vendor_document_lines()
        
        return result
    
    def _populate_vendor_document_lines(self):
        """Create document lines for all required document types.
        
        This creates placeholder document records so sales reps only need
        to upload the PDF files instead of remembering each document type.
        """
        self.ensure_one()
        if self.supplier_rank <= 0:
            return
        
        # Get all required document types
        doc_types = self.env["ptt.document.type"].search([("required", "=", True)])
        
        # Get existing document type IDs for this vendor
        existing_type_ids = set(self.ptt_vendor_document_ids.mapped("document_type_id").ids)
        
        # Create document lines for missing types
        VendorDocument = self.env["ptt.vendor.document"]
        for doc_type in doc_types:
            if doc_type.id not in existing_type_ids:
                VendorDocument.create({
                    "vendor_id": self.id,
                    "document_type_id": doc_type.id,
                    "status": "non_compliant",  # Default until document is uploaded
                })
    
    # === VENDOR RATING ===
    ptt_vendor_rating = fields.Selection(
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
