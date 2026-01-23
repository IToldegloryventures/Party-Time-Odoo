from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ResPartner(models.Model):
    """Extend res.partner for PTT vendor management fields.
    
    This module adds vendor-specific fields and functionality to partners.
    
    VENDOR IDENTIFICATION:
    - Uses native Odoo supplier_rank field (supplier_rank > 0 = vendor)
    - When supplier_rank > 0, partner appears in Vendor Management app
    
    VENDOR STATUS WORKFLOW:
    - new → pending_review → active → inactive
    - Vendors must complete onboarding before activation
    
    FIELD NAMING:
    - All custom fields use ptt_ prefix (Party Time Texas)
    - This follows Odoo best practice: x_ is reserved for Studio fields
    
    PERFORMANCE:
    - Required document types are cached per-environment to avoid repeated searches
    - Compliance computation only runs for vendors (supplier_rank > 0)
    """
    _inherit = "res.partner"

    # === VENDOR STATUS WORKFLOW ===
    ptt_vendor_status = fields.Selection(
        [
            ("new", "New"),
            ("pending_review", "Pending Review"),
            ("active", "Active"),
            ("inactive", "Inactive"),
        ],
        string="Vendor Status",
        default="new",
        tracking=True,
        help="Vendor onboarding status workflow",
    )
    
    ptt_portal_user_id = fields.Many2one(
        "res.users",
        string="Portal User",
        help="Portal user account for this vendor",
    )

    # === VENDOR WORK ORDER HISTORY ===
    ptt_vendor_assignment_ids = fields.One2many(
        "ptt.project.vendor.assignment",
        "vendor_id",
        string="Work Order Assignments",
        help="All work orders assigned to this vendor",
    )
    
    ptt_assignment_count = fields.Integer(
        string="Work Orders",
        compute="_compute_vendor_assignment_stats",
        help="Total number of work orders assigned to this vendor",
    )
    
    ptt_completed_assignment_count = fields.Integer(
        string="Completed",
        compute="_compute_vendor_assignment_stats",
        help="Number of completed work orders",
    )

    ptt_active_assignment_count = fields.Integer(
        string="Active Work Orders",
        compute="_compute_vendor_assignment_stats",
        help="Number of active work orders (pending/confirmed)",
    )

    ptt_vendor_portal_access = fields.Boolean(
        string="Portal Access",
        compute="_compute_vendor_portal_access",
        help="Indicates whether this vendor has an active portal user linked",
    )
    
    ptt_total_paid = fields.Monetary(
        string="Total Paid",
        compute="_compute_vendor_assignment_stats",
        currency_field="currency_id",
        help="Total amount paid to this vendor across all assignments",
    )
    
    ptt_average_cost = fields.Monetary(
        string="Average Cost",
        compute="_compute_vendor_assignment_stats",
        currency_field="currency_id",
        help="Average cost per completed assignment",
    )

    # === VENDOR SERVICES ===
    # Uses ptt_vendor_service_ids from ptt_business_core (links directly to products)
    
    # === SERVICE PRICING ===
    ptt_vendor_service_pricing_ids = fields.One2many(
        "ptt.vendor.service.pricing",
        "vendor_id",
        string="Service Pricing",
        help="Pricing for each service this vendor offers",
    )
    
    # Vendor Tier - migrated from gold/silver/bronze to essentials/classic/premier in v19.0.5.0.0
    ptt_vendor_tier = fields.Selection(
        [
            ("essentials", "Essentials"),
            ("classic", "Classic"),
            ("premier", "Premier"),
        ],
        string="Vendor Tier",
        help="Overall quality tier for this vendor. Used to match with product tiers when assigning vendors to quotes. Essentials=Basic, Classic=Standard, Premier=Premium.",
    )
    
    # === VENDOR CONTACT FIELDS ===
    ptt_vendor_contact_role = fields.Char(
        string="Role at Vendor",
        help="This person's role at the vendor company (e.g., Owner, Talent, Accounting)",
    )
    
    ptt_is_vendor_contact = fields.Boolean(
        string="Is Vendor Contact",
        help="Mark this contact as a contact person for a vendor company",
    )
    
    # === VENDOR ADDITIONAL INFO ===
    ptt_vendor_principal_name = fields.Char(
        string="Principal/Owner Name",
        help="Name of the business owner or principal",
    )
    
    ptt_vendor_additional_phone = fields.Char(
        string="Additional Phone",
        help="Secondary phone number",
    )
    
    ptt_vendor_fax = fields.Char(
        string="Fax",
        help="Fax number if applicable",
    )
    
    ptt_vendor_zip_radius = fields.Float(
        string="Service Radius (miles)",
        help="How far this vendor is willing to travel for events",
    )

    # === VENDOR DOCUMENT RELATION ===
    ptt_vendor_document_ids = fields.One2many(
        "ptt.vendor.document",
        "vendor_id",
        string="Vendor Documents",
        help="Documents uploaded by or for this vendor",
    )
    
    # === ALL DOCUMENTS (vendor + contacts) ===
    ptt_all_document_ids = fields.One2many(
        "ptt.vendor.document",
        string="All Documents",
        compute="_compute_all_documents",
        help="All documents for this vendor and their contacts",
    )
    
    ptt_vendor_document_count = fields.Integer(
        string="Vendor Docs",
        compute="_compute_vendor_document_count",
    )
    
    # === VENDOR CONTACTS (child contacts that are vendor contacts) ===
    ptt_vendor_contact_ids = fields.One2many(
        "res.partner",
        "parent_id",
        string="Vendor Contacts",
        domain="[('ptt_is_vendor_contact', '=', True)]",
        help="Contact persons for this vendor company",
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

    ptt_primary_vendor_contact_id = fields.Many2one(
        "res.partner",
        string="Primary Vendor Contact",
        compute="_compute_primary_vendor_contact",
        help="Primary contact for this vendor company",
    )

    ptt_primary_vendor_contact_email = fields.Char(
        string="Primary Contact Email",
        compute="_compute_primary_vendor_contact",
    )

    ptt_primary_vendor_contact_phone = fields.Char(
        string="Primary Contact Phone",
        compute="_compute_primary_vendor_contact",
    )

    @api.depends("ptt_vendor_assignment_ids", "ptt_vendor_assignment_ids.status", 
                 "ptt_vendor_assignment_ids.actual_cost")
    def _compute_vendor_assignment_stats(self):
        """Compute vendor work order statistics."""
        for partner in self:
            assignments = partner.ptt_vendor_assignment_ids
            completed = assignments.filtered(lambda a: a.status == 'completed')
            active = assignments.filtered(lambda a: a.status in ('pending', 'confirmed'))
            
            partner.ptt_assignment_count = len(assignments)
            partner.ptt_completed_assignment_count = len(completed)
            partner.ptt_active_assignment_count = len(active)
            partner.ptt_total_paid = sum(completed.mapped('actual_cost'))
            partner.ptt_average_cost = (
                partner.ptt_total_paid / len(completed) if completed else 0.0
            )

    @api.depends("ptt_portal_user_id")
    def _compute_vendor_portal_access(self):
        """Compute whether the vendor has portal access."""
        for partner in self:
            partner.ptt_vendor_portal_access = bool(partner.ptt_portal_user_id)

    @api.depends("ptt_vendor_document_ids")
    def _compute_vendor_document_count(self):
        """Compute document count (non-stored field)."""
        for partner in self:
            partner.ptt_vendor_document_count = len(partner.ptt_vendor_document_ids)
    
    @api.depends("ptt_vendor_document_ids", "ptt_vendor_contact_ids.ptt_vendor_document_ids")
    def _compute_all_documents(self):
        """Compute all documents including contacts' documents."""
        for partner in self:
            all_docs = partner.ptt_vendor_document_ids
            for contact in partner.ptt_vendor_contact_ids:
                all_docs |= contact.ptt_vendor_document_ids
            partner.ptt_all_document_ids = all_docs

    @api.depends("ptt_vendor_contact_ids", "child_ids")
    def _compute_primary_vendor_contact(self):
        """Select a primary vendor contact for quick reference."""
        for partner in self:
            contact = partner.ptt_vendor_contact_ids[:1]
            if not contact:
                contact = partner.child_ids.filtered(lambda c: not c.is_company)[:1]
            contact = contact[:1]
            partner.ptt_primary_vendor_contact_id = contact
            partner.ptt_primary_vendor_contact_email = contact.email if contact else False
            partner.ptt_primary_vendor_contact_phone = contact.phone if contact else False

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
    
    # NOTE: ptt_vendor_notes and ptt_vendor_rating are defined in ptt_business_core
    # This module extends with document management and compliance tracking only
    
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
    
    # NOTE: ptt_vendor_rating is defined in ptt_business_core with different labels
    # This module uses the base definition
    
    # === ACTION METHODS ===
    def action_populate_document_lines(self):
        """Button action to populate missing document lines for this vendor.
        
        Use this for existing vendors who don't have document lines yet.
        """
        for vendor in self:
            if vendor.supplier_rank > 0:
                vendor._populate_vendor_document_lines()
        return True
    
    @api.model
    def action_populate_all_vendor_documents(self):
        """Server action to populate document lines for ALL existing vendors.
        
        Call this once after installing/updating to populate existing vendors.
        """
        vendors = self.search([("supplier_rank", ">", 0)])
        count = 0
        for vendor in vendors:
            existing_count = len(vendor.ptt_vendor_document_ids)
            vendor._populate_vendor_document_lines()
            if len(vendor.ptt_vendor_document_ids) > existing_count:
                count += 1
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Document Lines Populated",
                "message": f"Populated document lines for {count} vendors.",
                "sticky": False,
                "type": "success",
            }
        }
    
    # === VENDOR STATUS WORKFLOW ACTIONS ===
    
    def action_submit_for_review(self):
        """Vendor submits their application for review.
        
        Validates that required fields are filled before submission.
        """
        for vendor in self:
            if vendor.supplier_rank <= 0:
                raise UserError(_("This contact is not marked as a vendor."))
            
            # Validate required fields
            vendor._validate_vendor_required_fields()
            
            vendor.ptt_vendor_status = "pending_review"
            vendor.message_post(
                body=_("Vendor application submitted for review."),
                message_type="notification",
            )
        return True
    
    def action_approve_vendor(self):
        """Approve vendor and set status to active."""
        for vendor in self:
            if vendor.supplier_rank <= 0:
                raise UserError(_("This contact is not marked as a vendor."))
            
            vendor.ptt_vendor_status = "active"
            vendor.message_post(
                body=_("Vendor approved and activated."),
                message_type="notification",
            )
        return True
    
    def action_request_info(self):
        """Request additional information from vendor."""
        for vendor in self:
            if vendor.supplier_rank <= 0:
                raise UserError(_("This contact is not marked as a vendor."))
            
            vendor.ptt_vendor_status = "new"
            vendor.message_post(
                body=_("Additional information requested. Please update your vendor profile."),
                message_type="notification",
            )
            
            # Send email if vendor has portal user
            if vendor.ptt_portal_user_id and vendor.email:
                template = self.env.ref(
                    "ptt_vendor_management.email_template_vendor_info_request",
                    raise_if_not_found=False
                )
                if template:
                    template.send_mail(vendor.id, force_send=True)
        return True
    
    def action_deactivate_vendor(self):
        """Deactivate vendor."""
        for vendor in self:
            vendor.ptt_vendor_status = "inactive"
            vendor.message_post(
                body=_("Vendor deactivated."),
                message_type="notification",
            )
        return True
    
    def action_reactivate_vendor(self):
        """Reactivate vendor after validating documents."""
        for vendor in self:
            if vendor.supplier_rank <= 0:
                raise UserError(_("This contact is not marked as a vendor."))
            
            # Check document validity
            vendor._validate_document_validity()
            
            vendor.ptt_vendor_status = "active"
            vendor.message_post(
                body=_("Vendor reactivated."),
                message_type="notification",
            )
        return True
    
    # === PORTAL USER MANAGEMENT ===
    
    def action_grant_portal_access(self):
        """Create or grant portal access to this vendor.
        
        Creates a portal user if one doesn't exist, or sends invitation.
        """
        self.ensure_one()
        
        if self.supplier_rank <= 0:
            raise UserError(_("This contact is not marked as a vendor."))
        
        if not self.name or not self.email:
            raise UserError(_("Vendor must have a name and email to create portal access."))
        
        # Check if user already exists with this email
        existing_user = self.env["res.users"].sudo().search([
            ("login", "=", self.email)
        ], limit=1)
        
        if existing_user:
            self.ptt_portal_user_id = existing_user.id
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Portal User Exists"),
                    "message": _("User already exists with this email. Linked to vendor."),
                    "type": "warning",
                    "sticky": False,
                }
            }
        
        # Create portal user
        portal_group = self.env.ref("base.group_portal")
        user_vals = {
            "name": self.name,
            "login": self.email,
            "email": self.email,
            "partner_id": self.id,
            "groups_id": [(6, 0, [portal_group.id])],
            "active": True,
            "company_id": self.company_id.id or self.env.company.id,
        }
        
        new_user = self.env["res.users"].sudo().create(user_vals)
        self.ptt_portal_user_id = new_user.id
        
        # Send portal welcome email
        template = self.env.ref("portal.mail_template_data_portal_welcome", raise_if_not_found=False)
        if template:
            template.sudo().send_mail(new_user.id, force_send=True)
        
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Portal Access Granted"),
                "message": _("Portal invitation sent to %s") % self.email,
                "type": "success",
                "sticky": False,
            }
        }
    
    def action_view_vendor_documents(self):
        """Open the documents view for this vendor."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Vendor Documents - %s") % self.name,
            "res_model": "ptt.vendor.document",
            "view_mode": "list,form",
            "domain": ["|", ("vendor_id", "=", self.id), ("vendor_id", "in", self.ptt_vendor_contact_ids.ids)],
            "context": {
                "default_vendor_id": self.id,
                "search_default_group_by_type": 1,
            },
        }
    
    def action_view_vendor_work_orders(self):
        """Open the work order assignments for this vendor."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Work Orders - %s") % self.name,
            "res_model": "ptt.project.vendor.assignment",
            "view_mode": "list,form",
            "domain": [("vendor_id", "=", self.id)],
            "context": {
                "default_vendor_id": self.id,
            },
        }

    def action_view_vendor_assignments(self):
        """Backward-compatible alias for vendor work order smart button."""
        return self.action_view_vendor_work_orders()
    
    # === VALIDATION METHODS ===
    
    def _validate_vendor_required_fields(self):
        """Validate that all required vendor fields are filled."""
        self.ensure_one()
        
        if not self.name:
            raise UserError(_("Company/Vendor name is required."))
        
        if not self.email:
            raise UserError(_("Email is required."))
        
        # Check for at least one service
        if not self.ptt_vendor_service_ids and not self.ptt_vendor_service_pricing_ids:
            raise UserError(_("At least one service must be selected."))
        
        return True
    
    def _validate_document_validity(self):
        """Validate that no required documents are expired."""
        self.ensure_one()
        
        today = fields.Date.today()
        
        # Check vendor documents
        expired_docs = self.ptt_vendor_document_ids.filtered(
            lambda d: d.document_type_id.required and d.validity and d.validity < today
        )
        
        # Check contact documents
        for contact in self.ptt_vendor_contact_ids:
            expired_docs |= contact.ptt_vendor_document_ids.filtered(
                lambda d: d.document_type_id.required and d.validity and d.validity < today
            )
        
        if expired_docs:
            doc_names = ", ".join(expired_docs.mapped("document_type_id.name"))
            raise UserError(
                _("The following required documents are expired: %s. Please update them before reactivating.") % doc_names
            )
        
        return True
