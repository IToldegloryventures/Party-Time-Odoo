from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta


class PttVendorDocument(models.Model):
    """Vendor documents with expiry tracking"""
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
    
    # Status
    status = fields.Selection(
        [
            ("valid", "Valid"),
            ("expiring_soon", "Expiring Soon"),
            ("expired", "Expired"),
            ("not_applicable", "N/A"),
        ],
        string="Status",
        compute="_compute_status",
        store=True,
        help="Document validity status",
    )
    
    notes = fields.Text(
        string="Notes",
        help="Additional notes about this document",
    )
    
    @api.depends("validity", "document_type_id.expiry_warning_days", "document_type_id.has_expiry")
    def _compute_status(self):
        """Compute document status based on expiry date."""
        today = fields.Date.today()
        for doc in self:
            if not doc.document_type_id.has_expiry or not doc.validity:
                doc.status = "not_applicable"
            elif doc.validity < today:
                doc.status = "expired"
            elif doc.validity <= today + timedelta(days=doc.document_type_id.expiry_warning_days or 30):
                doc.status = "expiring_soon"
            else:
                doc.status = "valid"
    
    @api.constrains("vendor_id", "document_type_id")
    def _check_unique_vendor_doctype(self):
        """Ensure each vendor can only have one document per type."""
        for record in self:
            existing = self.search([
                ("vendor_id", "=", record.vendor_id.id),
                ("document_type_id", "=", record.document_type_id.id),
                ("id", "!=", record.id),
            ])
            if existing:
                raise ValidationError(
                    _("Each vendor can only have one document per type. Update the existing one.")
                )
    
    @api.model
    def _cron_check_document_expiry_30day(self):
        """Alert vendors with documents expiring in 30 days."""
        # Recompute status first
        self.search([])._compute_status()
        
        today = fields.Date.today()
        warning_date = today + timedelta(days=30)
        
        expiring_docs = self.search([
            ("validity", ">=", today),
            ("validity", "<=", warning_date),
            ("status", "=", "expiring_soon"),
        ])
        
        todo_activity_type = self.env.ref("mail.mail_activity_type_todo", raise_if_not_found=False)
        
        for doc in expiring_docs:
            if doc.vendor_id.email and todo_activity_type:
                # Create activity for vendor's portal user or admin
                # Note: portal_user_id field will be added in Phase 2
                user_id = self.env.ref("base.user_admin").id
                doc.vendor_id.activity_schedule(
                    activity_type_id=todo_activity_type.id,
                    summary=_("Document Expiring Soon: %s", doc.document_type_id.name),
                    note=_("Your %s expires on %s. Please upload a renewed document.",
                           doc.document_type_id.name, doc.validity),
                    user_id=user_id,
                )
    
    @api.model
    def _cron_check_document_expiry_7day(self):
        """Alert vendors with documents expiring in 7 days."""
        # Recompute status first
        self.search([])._compute_status()
        
        today = fields.Date.today()
        warning_date = today + timedelta(days=7)
        
        expiring_docs = self.search([
            ("validity", ">=", today),
            ("validity", "<=", warning_date),
            ("status", "=", "expiring_soon"),
        ])
        
        todo_activity_type = self.env.ref("mail.mail_activity_type_todo", raise_if_not_found=False)
        
        for doc in expiring_docs:
            if doc.vendor_id.email and todo_activity_type:
                # Create urgent activity
                # Note: portal_user_id field will be added in Phase 2
                user_id = self.env.ref("base.user_admin").id
                doc.vendor_id.activity_schedule(
                    activity_type_id=todo_activity_type.id,
                    summary=_("URGENT: Document Expiring Soon: %s", doc.document_type_id.name),
                    note=_("Your %s expires on %s. Please upload a renewed document immediately.",
                           doc.document_type_id.name, doc.validity),
                    user_id=user_id,
                )
    
    @api.model
    def _cron_check_document_expired(self):
        """Handle expired documents - deactivate vendors if required docs expired."""
        # Recompute status first
        self.search([])._compute_status()
        
        today = fields.Date.today()
        
        expired_docs = self.search([
            ("validity", "<", today),
            ("status", "=", "expired"),
        ])
        
        for doc in expired_docs:
            vendor = doc.vendor_id
            if doc.document_type_id.required:
                # If required document expired, deactivate vendor
                # Note: x_vendor_status field will be added in Phase 2
                # For now, just post a message
                vendor.message_post(
                    body=_("Vendor deactivated: Required document '%s' expired on %s.",
                           doc.document_type_id.name, doc.validity),
                )
