from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta


class PttVendorDocument(models.Model):
    """Vendor documents with expiry tracking.
    
    SUPPORTS BOTH VENDOR AND CONTACT-LEVEL DOCUMENTS:
    - vendor_id: The parent vendor company
    - contact_id: Optional specific contact the document belongs to
    
    PERFORMANCE OPTIMIZATIONS:
    - Cron jobs only query documents in their specific expiry windows
    - No full-table recomputation on cron runs
    - Status computed on-demand with proper depends decorators
    
    Reference: https://www.odoo.com/documentation/19.0/developer/reference/backend/orm.html
    """
    _name = "ptt.vendor.document"
    _description = "Vendor Document"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "vendor_id, document_type_id"

    vendor_id = fields.Many2one(
        "res.partner",
        string="Vendor",
        required=True,
        ondelete="cascade",
        domain="[('supplier_rank', '>', 0)]",
        index=True,
        tracking=True,
    )
    
    contact_id = fields.Many2one(
        "res.partner",
        string="Contact",
        ondelete="cascade",
        index=True,
        help="If set, this document belongs to this specific contact under the vendor",
    )
    
    document_owner = fields.Selection(
        [
            ("vendor", "Vendor"),
            ("contact", "Contact"),
        ],
        string="Document Owner",
        compute="_compute_document_owner",
        store=True,
        help="Indicates whether document belongs to vendor company or a contact",
    )
    
    contact_name = fields.Char(
        string="Contact Name",
        related="contact_id.name",
        store=True,
        readonly=True,
    )
    
    document_type_id = fields.Many2one(
        "ptt.document.type",
        string="Document Type",
        required=True,
        index=True,
        tracking=True,
    )
    
    # Document Storage
    attached_document = fields.Binary(
        string="Document File",
        attachment=True,
        help="Upload the document file",
    )
    
    document_filename = fields.Char(
        string="Filename",
        help="Name of the uploaded file",
    )
    
    @api.depends("vendor_id", "contact_id")
    def _compute_document_owner(self):
        """Compute whether document belongs to vendor or contact."""
        for doc in self:
            if doc.contact_id:
                doc.document_owner = "contact"
            else:
                doc.document_owner = "vendor"
    
    @api.constrains("vendor_id", "contact_id")
    def _check_contact_belongs_to_vendor(self):
        """Ensure contact belongs to the vendor company."""
        for doc in self:
            if doc.contact_id and doc.vendor_id:
                if doc.contact_id.parent_id.id != doc.vendor_id.id:
                    raise ValidationError(
                        _("Contact must belong to the selected vendor company.")
                    )
    
    @api.onchange("contact_id")
    def _onchange_contact_id(self):
        """Auto-set vendor when contact is selected."""
        if self.contact_id and self.contact_id.parent_id:
            self.vendor_id = self.contact_id.parent_id
    
    # Dates
    validity = fields.Date(
        string="Expiry Date",
        tracking=True,
        help="Date when this document expires (if applicable)",
    )
    
    upload_date = fields.Datetime(
        string="Upload Date",
        default=fields.Datetime.now,
        readonly=True,
        help="When this document was uploaded",
    )
    
    uploaded_by = fields.Many2one(
        "res.users",
        string="Uploaded By",
        default=lambda self: self.env.user,
        readonly=True,
        help="User who uploaded this document",
    )
    
    # Status - Manual selection for now, can automate based on expiry later
    status = fields.Selection(
        [
            ("compliant", "Compliant"),
            ("expiring_soon", "Expiring Soon"),
            ("non_compliant", "Non-Compliant"),
        ],
        string="Status",
        default="non_compliant",
        tracking=True,
        help="Document compliance status. Set manually by sales rep.",
    )
    
    notes = fields.Text(
        string="Notes",
        help="Additional notes about this document",
    )
    
    # NOTE: Status is now manual. This computed method is kept for future automation.
    # To re-enable automated status, change status field to compute="_compute_status", store=True
    # and uncomment this method:
    #
    # @api.depends("validity", "document_type_id.expiry_warning_days", "document_type_id.has_expiry")
    # def _compute_status(self):
    #     """Compute document status based on expiry date."""
    #     today = fields.Date.today()
    #     for doc in self:
    #         if not doc.validity:
    #             doc.status = "non_compliant"
    #         elif doc.validity < today:
    #             doc.status = "non_compliant"  
    #         elif doc.validity <= today + timedelta(days=doc.document_type_id.expiry_warning_days or 30):
    #             doc.status = "expiring_soon"
    #         else:
    #             doc.status = "compliant"
    
    @api.constrains("vendor_id", "document_type_id", "contact_id")
    def _check_unique_vendor_doctype(self):
        """Ensure document uniqueness per vendor/contact and type.
        
        Uniqueness scope:
        - Vendor-level documents: unique per vendor + document_type
        - Contact-level documents: unique per vendor + contact + document_type
        
        This allows a vendor to have a W9 and each contact to also have their own W9.
        """
        for record in self:
            domain = [
                ("vendor_id", "=", record.vendor_id.id),
                ("document_type_id", "=", record.document_type_id.id),
                ("id", "!=", record.id),
            ]
            
            # Include contact_id in uniqueness check
            # None/False values should be compared equally
            if record.contact_id:
                domain.append(("contact_id", "=", record.contact_id.id))
            else:
                domain.append(("contact_id", "=", False))
            
            existing = self.search(domain)
            if existing:
                if record.contact_id:
                    raise ValidationError(
                        _("This contact already has a document of this type. Update the existing one.")
                    )
                else:
                    raise ValidationError(
                        _("This vendor already has a document of this type. Update the existing one.")
                    )
    
    @api.model
    def _cron_check_document_expiry_30day(self):
        """Alert vendors with documents expiring in 30 days.
        
        PERFORMANCE: Only searches documents in the 30-day expiry window.
        """
        today = fields.Date.today()
        warning_date = today + timedelta(days=30)
        
        # Find documents expiring in 30 days
        expiring_docs = self.search([
            ("document_type_id.has_expiry", "=", True),
            ("validity", ">=", today),
            ("validity", "<=", warning_date),
        ])
        
        todo_activity_type = self.env.ref("mail.mail_activity_type_todo", raise_if_not_found=False)
        
        for doc in expiring_docs:
            # Auto-update status to expiring_soon
            if doc.status == "compliant":
                doc.status = "expiring_soon"
            
            if doc.vendor_id.email and todo_activity_type:
                user_id = self.env.ref("base.user_admin").id
                existing_activity = self.env["mail.activity"].search([
                    ("res_model", "=", "res.partner"),
                    ("res_id", "=", doc.vendor_id.id),
                    ("activity_type_id", "=", todo_activity_type.id),
                    ("summary", "ilike", doc.document_type_id.name),
                ], limit=1)
                
                if not existing_activity:
                    doc.vendor_id.activity_schedule(
                        activity_type_id=todo_activity_type.id,
                        summary=_("Document Expiring Soon: %s", doc.document_type_id.name),
                        note=_("Vendor %s: Document '%s' expires on %s. Please request a renewed document.",
                               doc.vendor_id.name, doc.document_type_id.name, doc.validity),
                        user_id=user_id,
                    )
    
    @api.model
    def _cron_check_document_expiry_7day(self):
        """Alert vendors with documents expiring in 7 days (urgent)."""
        today = fields.Date.today()
        warning_date = today + timedelta(days=7)
        
        expiring_docs = self.search([
            ("document_type_id.has_expiry", "=", True),
            ("validity", ">=", today),
            ("validity", "<=", warning_date),
        ])
        
        todo_activity_type = self.env.ref("mail.mail_activity_type_todo", raise_if_not_found=False)
        
        for doc in expiring_docs:
            # Auto-update status to expiring_soon
            if doc.status == "compliant":
                doc.status = "expiring_soon"
            
            if doc.vendor_id.email and todo_activity_type:
                user_id = self.env.ref("base.user_admin").id
                existing_activity = self.env["mail.activity"].search([
                    ("res_model", "=", "res.partner"),
                    ("res_id", "=", doc.vendor_id.id),
                    ("activity_type_id", "=", todo_activity_type.id),
                    ("summary", "ilike", "URGENT"),
                    ("summary", "ilike", doc.document_type_id.name),
                ], limit=1)
                
                if not existing_activity:
                    doc.vendor_id.activity_schedule(
                        activity_type_id=todo_activity_type.id,
                        summary=_("URGENT: Document Expiring Soon: %s", doc.document_type_id.name),
                        note=_("Vendor %s: Document '%s' expires on %s. Please request a renewed document immediately.",
                               doc.vendor_id.name, doc.document_type_id.name, doc.validity),
                        user_id=user_id,
                    )
    
    @api.model
    def _cron_check_document_expired(self):
        """Handle expired documents - auto-set to non-compliant and alert."""
        today = fields.Date.today()
        
        expired_docs = self.search([
            ("document_type_id.has_expiry", "=", True),
            ("document_type_id.required", "=", True),
            ("validity", "<", today),
            ("status", "!=", "non_compliant"),  # Only update if not already non-compliant
        ])
        
        for doc in expired_docs:
            # Auto-update status to non-compliant
            doc.status = "non_compliant"
            
            vendor = doc.vendor_id
            today_str = today.strftime("%Y-%m-%d")
            recent_messages = vendor.message_ids.filtered(
                lambda m: m.date.strftime("%Y-%m-%d") == today_str and 
                         doc.document_type_id.name in (m.body or "")
            )
            
            if not recent_messages:
                vendor.message_post(
                    body=_("Warning: Required document '%s' expired on %s. Vendor compliance status affected.",
                           doc.document_type_id.name, doc.validity),
                    message_type="notification",
                )
