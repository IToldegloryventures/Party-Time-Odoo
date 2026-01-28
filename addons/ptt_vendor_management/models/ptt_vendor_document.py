# -*- coding: utf-8 -*-
from datetime import timedelta

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PttVendorDocument(models.Model):
    """Vendor documents with expiry tracking for vendors and contacts."""

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
        [("vendor", "Vendor"), ("contact", "Contact")],
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

    # Document Storage - Odoo 19 native ir.attachment system
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'ptt_vendor_document_attachment_rel',
        'document_id',
        'attachment_id',
        string="Attachments",
        help="Document files attached to this record",
    )
    
    # Legacy Binary field (kept for backward compatibility, but attachment_ids is preferred)
    attached_document = fields.Binary(
        string="Document File (Legacy)",
        attachment=True,
        help="Legacy single file upload. Use Attachments field for multiple files.",
    )
    document_filename = fields.Char(
        string="Filename (Legacy)",
        help="Name of the uploaded file (legacy field)",
    )

    # Dates / Status
    validity = fields.Date(
        string="Expiry Date",
        tracking=True,
        help="Date when this document expires (if applicable)",
    )
    status = fields.Selection(
        [
            ("compliant", "Compliant"),
            ("expiring_soon", "Expiring Soon"),
            ("non_compliant", "Non-Compliant"),
        ],
        string="Status",
        compute="_compute_status",
        store=True,
        tracking=True,
        default="non_compliant",
        help="Document compliance status. Computed from expiry and requirements.",
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

    notes = fields.Text(
        string="Notes",
        help="Additional notes about this document",
    )

    _sql_constraints = [
        (
            'unique_vendor_document',
            'unique(vendor_id, document_type_id, contact_id)',
            'Each vendor/contact can only have one document of each type.'
        ),
    ]

    @api.depends("vendor_id", "contact_id")
    def _compute_document_owner(self):
        """Compute whether document belongs to vendor or contact."""
        for doc in self:
            doc.document_owner = "contact" if doc.contact_id else "vendor"

    @api.constrains("vendor_id", "contact_id")
    def _check_contact_belongs_to_vendor(self):
        """Ensure contact belongs to the vendor company."""
        for doc in self:
            if doc.contact_id and doc.vendor_id:
                if doc.contact_id.parent_id.id != doc.vendor_id.id:
                    raise ValidationError(_("Contact must belong to the selected vendor company."))

    @api.onchange("contact_id")
    def _onchange_contact_id(self):
        """Auto-set vendor when contact is selected."""
        if self.contact_id and self.contact_id.parent_id:
            self.vendor_id = self.contact_id.parent_id

    @api.depends("validity", "document_type_id.expiry_warning_days", "document_type_id.has_expiry", "attachment_ids", "attached_document")
    def _compute_status(self):
        """Compute document status based on expiry date and requirements."""
        today = fields.Date.today()
        for doc in self:
            # Check if document has any attachments (prefer attachment_ids, fallback to attached_document)
            has_attachment = bool(doc.attachment_ids) or bool(doc.attached_document)
            
            if doc.document_type_id.has_expiry:
                if not doc.validity:
                    doc.status = "non_compliant"
                elif doc.validity < today:
                    doc.status = "non_compliant"
                elif doc.validity <= today + timedelta(days=doc.document_type_id.expiry_warning_days or 30):
                    doc.status = "expiring_soon"
                else:
                    doc.status = "compliant" if has_attachment else "non_compliant"
            else:
                doc.status = "compliant" if has_attachment else "non_compliant"

    @api.constrains("vendor_id", "document_type_id", "contact_id")
    def _check_unique_vendor_doctype(self):
        """Ensure document uniqueness per vendor/contact and type."""
        for record in self:
            domain = [
                ("vendor_id", "=", record.vendor_id.id),
                ("document_type_id", "=", record.document_type_id.id),
                ("id", "!=", record.id),
            ]
            if record.contact_id:
                domain.append(("contact_id", "=", record.contact_id.id))
            else:
                domain.append(("contact_id", "=", False))

            if self.search(domain, limit=1):
                if record.contact_id:
                    raise ValidationError(_("This contact already has a document of this type. Update the existing one."))
                else:
                    raise ValidationError(_("This vendor already has a document of this type. Update the existing one."))
