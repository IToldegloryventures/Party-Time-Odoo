from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import timedelta


class ResPartner(models.Model):
    _inherit = "res.partner"

    # === VENDOR FIELDS ===
    x_is_vendor = fields.Boolean(
        string="Vendor",
        help="Mark this contact as a vendor / service provider.",
    )
    
    # Vendor Status & Workflow
    x_vendor_status = fields.Selection(
        [
            ("new", "New"),
            ("pending_review", "Pending Review"),
            ("active", "Active"),
            ("inactive", "Inactive"),
            ("denied", "Denied"),
        ],
        string="Vendor Status",
        default="new",
        tracking=True,
        help="Current status of vendor application/review process",
    )
    
    portal_user_id = fields.Many2one(
        "res.users",
        string="Portal User",
        help="Portal user account for this vendor",
    )
    
    x_vendor_tier = fields.Selection(
        [
            ("preferred", "Preferred"),
            ("qualified", "Qualified"),
            ("unqualified", "Unqualified"),
        ],
        string="Vendor Tier",
        default="qualified",
        help="Vendor qualification tier",
    )
    
    # Vendor Detail Fields
    x_vendor_service_types = fields.Selection(
        [
            ("dj", "DJ/MC Services"),
            ("photovideo", "Photo/Video"),
            ("live_entertainment", "Live Entertainment"),
            ("lighting", "Lighting/AV"),
            ("decor", "Decor/Thematic Design"),
            ("photobooth", "Photo Booth"),
            ("caricature", "Caricature Artists"),
            ("casino", "Casino Services"),
            ("catering", "Catering"),
            ("transportation", "Transportation"),
            ("rentals", "Rentals (Other)"),
            ("staffing", "Staffing"),
            ("venue_sourcing", "Venue Sourcing"),
            ("coordination", "Event Coordination"),
            ("other", "Other"),
        ],
        string="Service Type",
        help="Primary service type this vendor provides",
    )
    x_vendor_rating = fields.Selection(
        [
            ("1", "⭐"),
            ("2", "⭐⭐"),
            ("3", "⭐⭐⭐"),
            ("4", "⭐⭐⭐⭐"),
            ("5", "⭐⭐⭐⭐⭐"),
        ],
        string="Rating",
        help="Vendor performance rating",
    )
    x_vendor_notes = fields.Text(
        string="Vendor Notes",
        help="Additional notes about this vendor",
    )
    x_vendor_preferred = fields.Boolean(
        string="Preferred Vendor",
        help="Mark as preferred vendor for priority assignment",
    )
    
    # Vendor Restrictions
    x_vendor_restriction_ids = fields.Many2many(
        "ptt.vendor.restriction",
        string="Vendor Restrictions",
        help="Event types this vendor cannot service",
    )
    
    # Vendor Services & Pricing (One2many)
    x_vendor_service_ids = fields.One2many(
        "ptt.vendor.service",
        "vendor_id",
        string="Services & Pricing",
    )
    
    # Vendor Documents (One2many)
    x_vendor_document_ids = fields.One2many(
        "ptt.vendor.document",
        "vendor_id",
        string="Documents",
    )
    
    # Computed Fields
    x_vendor_document_status = fields.Selection(
        [
            ("ok", "All Documents Valid"),
            ("warning", "Documents Expiring Soon"),
            ("expired", "Documents Expired"),
            ("missing", "Required Documents Missing"),
        ],
        string="Document Status",
        compute="_compute_document_status",
        help="Overall document compliance status",
    )
    
    x_vendor_can_work = fields.Boolean(
        string="Can Accept Work",
        compute="_compute_can_work",
        help="True if vendor is active with valid documents",
    )
    
    # Stat button counts
    vendor_assignment_count = fields.Integer(
        string="Assignments",
        compute="_compute_vendor_assignment_count",
    )
    vendor_document_count = fields.Integer(
        string="Document Count",
        compute="_compute_vendor_document_count",
    )
    vendor_service_count = fields.Integer(
        string="Services",
        compute="_compute_vendor_service_count",
    )
    
    @api.depends("x_is_vendor")
    def _compute_vendor_assignment_count(self):
        """Count vendor assignments."""
        for partner in self:
            if partner.x_is_vendor:
                partner.vendor_assignment_count = self.env["ptt.project.vendor.assignment"].search_count([
                    ("vendor_id", "=", partner.id)
                ])
            else:
                partner.vendor_assignment_count = 0
    
    @api.depends("x_vendor_document_ids")
    def _compute_vendor_document_count(self):
        """Count vendor documents."""
        for partner in self:
            partner.vendor_document_count = len(partner.x_vendor_document_ids)
    
    @api.depends("x_vendor_service_ids")
    def _compute_vendor_service_count(self):
        """Count vendor services."""
        for partner in self:
            partner.vendor_service_count = len(partner.x_vendor_service_ids)
    
    # === VENDOR MANAGEMENT ACTIONS ===
    
    def action_vendor_approve(self):
        """Approve vendor and activate."""
        for record in self:
            if not record.x_is_vendor:
                raise UserError(_("This partner is not a vendor."))
            record.write({"x_vendor_status": "active"})
            record.message_post(
                body=_("Vendor approved and activated."),
                subtype_xmlid="mail.mt_note",
            )
    
    def action_vendor_deny(self):
        """Deny vendor application."""
        for record in self:
            if not record.x_is_vendor:
                raise UserError(_("This partner is not a vendor."))
            record.write({"x_vendor_status": "denied"})
            record.message_post(
                body=_("Vendor application denied."),
                subtype_xmlid="mail.mt_note",
            )
    
    def action_vendor_deactivate(self):
        """Deactivate vendor."""
        for record in self:
            if not record.x_is_vendor:
                raise UserError(_("This partner is not a vendor."))
            record.write({"x_vendor_status": "inactive"})
            record.message_post(
                body=_("Vendor deactivated."),
                subtype_xmlid="mail.mt_note",
            )
    
    def action_vendor_reactivate(self):
        """Reactivate vendor."""
        for record in self:
            if not record.x_is_vendor:
                raise UserError(_("This partner is not a vendor."))
            if record.x_vendor_document_status == "expired":
                raise UserError(_("Please update expired documents before reactivating."))
            record.write({"x_vendor_status": "active"})
            record.message_post(
                body=_("Vendor reactivated."),
                subtype_xmlid="mail.mt_note",
            )
    
    def action_vendor_grant_portal_access(self):
        """Grant portal access to vendor."""
        self.ensure_one()
        if not self.x_is_vendor:
            raise UserError(_("This partner is not a vendor."))
        if not self.name or not self.email:
            raise UserError(_("Please provide name and email for the vendor."))
        
        # Check if user already exists
        user = self.env["res.users"].sudo().search([("email", "=", self.email)], limit=1)
        if not user:
            # Create portal user
            user = self.env["res.users"].sudo().create({
                "name": self.name,
                "login": self.email,
                "email": self.email,
                "partner_id": self.id,
                "groups_id": [(6, 0, [self.env.ref("base.group_portal").id])],
            })
            # Send welcome email
            template = self.env.ref("portal.mail_template_data_portal_welcome", raise_if_not_found=False)
            if template:
                template.sudo().send_mail(user.id, force_send=True)
        
        self.write({"portal_user_id": user.id})
        self.message_post(
            body=_("Portal access granted. Welcome email sent."),
            subtype_xmlid="mail.mt_note",
        )
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Success"),
                "message": _("Portal access granted. Welcome email sent."),
                "type": "success",
            },
        }
    
    def action_view_vendor_assignments(self):
        """Open vendor assignments."""
        self.ensure_one()
        return {
            "name": _("Vendor Assignments"),
            "type": "ir.actions.act_window",
            "res_model": "ptt.project.vendor.assignment",
            "view_mode": "list,form",
            "domain": [("vendor_id", "=", self.id)],
            "context": {"default_vendor_id": self.id},
        }
    
    def action_view_vendor_documents(self):
        """Open vendor documents."""
        self.ensure_one()
        return {
            "name": _("Vendor Documents"),
            "type": "ir.actions.act_window",
            "res_model": "ptt.vendor.document",
            "view_mode": "list,form",
            "domain": [("vendor_id", "=", self.id)],
            "context": {"default_vendor_id": self.id},
        }
    
    def action_view_vendor_services(self):
        """Open vendor services."""
        self.ensure_one()
        return {
            "name": _("Vendor Services"),
            "type": "ir.actions.act_window",
            "res_model": "ptt.vendor.service",
            "view_mode": "list,form",
            "domain": [("vendor_id", "=", self.id)],
            "context": {"default_vendor_id": self.id},
        }
    
    @api.depends("x_vendor_document_ids", "x_vendor_document_ids.status")
    def _compute_document_status(self):
        """Compute overall document status for vendor."""
        for partner in self:
            if not partner.x_is_vendor or not partner.x_vendor_document_ids:
                partner.x_vendor_document_status = "missing"
                continue
            
            docs = partner.x_vendor_document_ids
            required_doc_types = self.env["ptt.document.type"].search([("required", "=", True)])
            
            # Check for missing required documents
            if required_doc_types:
                existing_types = docs.mapped("document_type_id")
                missing_types = required_doc_types - existing_types
                if missing_types:
                    partner.x_vendor_document_status = "missing"
                    continue
            
            # Check document statuses
            if any(doc.status == "expired" for doc in docs):
                partner.x_vendor_document_status = "expired"
            elif any(doc.status == "expiring_soon" for doc in docs):
                partner.x_vendor_document_status = "warning"
            else:
                partner.x_vendor_document_status = "ok"
    
    @api.depends("x_vendor_status", "x_vendor_document_status")
    def _compute_can_work(self):
        """Compute if vendor can accept work assignments."""
        for partner in self:
            partner.x_vendor_can_work = (
                partner.x_is_vendor
                and partner.x_vendor_status == "active"
                and partner.x_vendor_document_status in ("ok", "warning")
            )
