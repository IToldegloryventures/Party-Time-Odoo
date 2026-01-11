from odoo import models, fields, api


class ResPartner(models.Model):
    """Extend res.partner for PTT vendor management.
    
    NOTE: Use standard Odoo fields where possible:
    - supplier_rank > 0 = Is a Vendor (standard - use instead of x_is_vendor)
    - comment = Internal Notes (standard - use instead of x_vendor_notes)
    - is_company = True for vendor companies, False for contacts
    - parent_id = Link contacts to their vendor company
    
    Custom PTT fields are for vendor-specific data only.
    """
    _inherit = "res.partner"

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
    
    # === VENDOR CONTACT ROLE ===
    x_vendor_contact_role = fields.Char(
        string="Role at Vendor",
        help="This person's role at the vendor company (e.g., Owner, Talent, Accounting)",
    )

    # === VENDOR DOCUMENT RELATION ===
    x_vendor_document_ids = fields.One2many(
        "ptt.vendor.document",
        "vendor_id",
        string="Vendor Documents",
        help="Documents uploaded by or for this vendor",
    )
    
    x_vendor_document_count = fields.Integer(
        string="Document Count",
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
        help="Vendor document compliance status based on required documents",
    )

    @api.depends("x_vendor_document_ids", "x_vendor_document_ids.status", 
                 "x_vendor_document_ids.document_type_id.required")
    def _compute_vendor_compliance(self):
        """Compute vendor compliance status based on required documents."""
        required_doc_types = self.env["ptt.document.type"].search([("required", "=", True)])
        required_type_ids = set(required_doc_types.ids)
        
        for partner in self:
            partner.x_vendor_document_count = len(partner.x_vendor_document_ids)
            
            # Only compute compliance for vendors (supplier_rank > 0)
            if partner.supplier_rank == 0:
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

    # === VENDOR FIELDS (Custom PTT) ===
    x_vendor_service_types = fields.Selection(
        [
            ("dj", "DJ & MC Services"),
            ("photovideo", "Photo/Video"),
            ("live_entertainment", "Live Entertainment"),
            ("lighting", "Lighting/AV"),
            ("decor", "Decor/Thematic Design"),
            ("photobooth", "Photo Booth"),
            ("caricature", "Caricature Artist"),
            ("casino", "Casino Services"),
            ("catering", "Catering & Bartender Services"),
            ("transportation", "Transportation"),
            ("rentals", "Rentals (Other)"),
            ("staffing", "Staffing"),
            ("venue_sourcing", "Venue Sourcing"),
            ("coordination", "Event Planning Services"),
            ("other", "Other"),
        ],
        string="Service Type",
        help="Primary service type this vendor provides. Note: Use supplier_rank > 0 to identify vendors.",
    )
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
    x_vendor_preferred = fields.Boolean(
        string="Preferred Vendor",
        help="Mark as preferred vendor for priority assignment",
    )
