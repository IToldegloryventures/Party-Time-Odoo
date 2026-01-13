from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta


class PttVendorDocument(models.Model):
    """Vendor documents with expiry tracking.
    
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
        """Compute document status based on expiry date.
        
        This is a stored computed field that automatically recomputes when:
        - validity date changes
        - document type expiry settings change
        
        The store=True ensures status is persisted and searchable.
        """
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
        """Alert vendors with documents expiring in 30 days.
        
        PERFORMANCE: Only searches documents in the 30-day expiry window,
        not the entire table. No full-table status recomputation.
        
        Reference: https://www.odoo.com/documentation/19.0/developer/reference/backend/actions.html
        """
        today = fields.Date.today()
        warning_date = today + timedelta(days=30)
        
        # Only search documents that:
        # 1. Have expiry tracking enabled
        # 2. Expire between today and 30 days from now
        # 3. Haven't already expired
        expiring_docs = self.search([
            ("document_type_id.has_expiry", "=", True),
            ("validity", ">=", today),
            ("validity", "<=", warning_date),
        ])
        
        # Force recompute status only for these specific documents
        expiring_docs._compute_status()
        
        # Filter to only "expiring_soon" status after recompute
        expiring_docs = expiring_docs.filtered(lambda d: d.status == "expiring_soon")
        
        todo_activity_type = self.env.ref("mail.mail_activity_type_todo", raise_if_not_found=False)
        
        for doc in expiring_docs:
            if doc.vendor_id.email and todo_activity_type:
                # Create activity for admin to follow up
                user_id = self.env.ref("base.user_admin").id
                # Check if activity already exists to avoid duplicates
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
        """Alert vendors with documents expiring in 7 days.
        
        PERFORMANCE: Only searches documents in the 7-day expiry window,
        not the entire table. No full-table status recomputation.
        """
        today = fields.Date.today()
        warning_date = today + timedelta(days=7)
        
        # Only search documents expiring in next 7 days
        expiring_docs = self.search([
            ("document_type_id.has_expiry", "=", True),
            ("validity", ">=", today),
            ("validity", "<=", warning_date),
        ])
        
        # Force recompute status only for these specific documents
        expiring_docs._compute_status()
        
        # Filter to only "expiring_soon" status
        expiring_docs = expiring_docs.filtered(lambda d: d.status == "expiring_soon")
        
        todo_activity_type = self.env.ref("mail.mail_activity_type_todo", raise_if_not_found=False)
        
        for doc in expiring_docs:
            if doc.vendor_id.email and todo_activity_type:
                user_id = self.env.ref("base.user_admin").id
                # Check if urgent activity already exists
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
        """Handle expired documents - alert about vendors with expired required docs.
        
        PERFORMANCE: Only searches documents that have already expired,
        not the entire table. No full-table status recomputation.
        """
        today = fields.Date.today()
        
        # Only search documents that have expired and are required
        expired_docs = self.search([
            ("document_type_id.has_expiry", "=", True),
            ("document_type_id.required", "=", True),
            ("validity", "<", today),
        ])
        
        # Force recompute status only for these specific documents
        expired_docs._compute_status()
        
        # Filter to only "expired" status
        expired_docs = expired_docs.filtered(lambda d: d.status == "expired")
        
        for doc in expired_docs:
            vendor = doc.vendor_id
            # Post a message if not already posted today
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
