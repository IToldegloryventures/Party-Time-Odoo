# -*- coding: utf-8 -*-
"""
Vendor Portal Controller
========================
Provides portal access for vendors to view their assignments,
accept/decline work orders, communicate via chatter, and upload files.

Routes:
- /my/vendor-assignments: List all assignments for current vendor
- /my/vendor-assignments/<id>: View assignment details
- /my/vendor-assignments/<id>/accept: Accept assignment
- /my/vendor-assignments/<id>/decline: Decline assignment

Following Odoo 19 portal patterns from official documentation.
"""

import base64
import mimetypes
from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.exceptions import AccessError, MissingError, UserError

# Allowed file extensions for uploads (security)
ALLOWED_EXTENSIONS = {
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.png', '.jpg', '.jpeg', 
    '.gif', '.txt', '.csv', '.zip', '.w9'
}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


class VendorPortal(CustomerPortal):
    """Portal controller for vendor assignment management.
    
    Inherits from CustomerPortal to use standard Odoo 19 portal patterns
    including proper document access checks and page value preparation.
    """

    # === PORTAL HOME COUNTERS ===
    def _prepare_home_portal_values(self, counters):
        """Add vendor assignment count to portal home page.
        
        This is called by the portal home to display badge counts.
        """
        values = super()._prepare_home_portal_values(counters)
        if "vendor_assignment_count" in counters:
            partner = request.env.user.partner_id
            VendorAssignment = request.env["ptt.project.vendor.assignment"]
            values["vendor_assignment_count"] = VendorAssignment.search_count([
                ("vendor_id", "=", partner.id)
            ])
        return values

    # === ASSIGNMENT LIST VIEW ===
    @http.route(
        ["/my/vendor-assignments", "/my/vendor-assignments/page/<int:page>"],
        type="http",
        auth="user",
        website=True,
    )
    def portal_vendor_assignments(self, page=1, sortby=None, filterby=None, **kw):
        """Display list of vendor assignments for the current portal user."""
        VendorAssignment = request.env["ptt.project.vendor.assignment"]
        partner = request.env.user.partner_id

        # Define sorting options
        searchbar_sortings = {
            "date": {"label": _("Event Date"), "order": "x_event_date desc"},
            "status": {"label": _("Status"), "order": "x_status"},
            "service": {"label": _("Service Type"), "order": "service_type"},
        }
        if not sortby:
            sortby = "date"
        order = searchbar_sortings[sortby]["order"]

        # Define filter options
        searchbar_filters = {
            "all": {"label": _("All"), "domain": []},
            "pending": {"label": _("Pending Response"), "domain": [("x_status", "=", "pending")]},
            "accepted": {"label": _("Accepted"), "domain": [("x_status", "=", "accepted")]},
            "confirmed": {"label": _("Confirmed"), "domain": [("x_status", "=", "confirmed")]},
            "completed": {"label": _("Completed"), "domain": [("x_status", "=", "completed")]},
        }
        if not filterby:
            filterby = "all"

        # Build domain - vendor_id filter is enforced by record rules, but we add it explicitly too
        domain = [("vendor_id", "=", partner.id)] + searchbar_filters[filterby]["domain"]

        # Get total count for pager
        assignment_count = VendorAssignment.search_count(domain)

        # Pager
        pager = portal_pager(
            url="/my/vendor-assignments",
            url_args={"sortby": sortby, "filterby": filterby},
            total=assignment_count,
            page=page,
            step=10,
        )

        # Get assignments
        assignments = VendorAssignment.search(
            domain,
            order=order,
            limit=10,
            offset=pager["offset"],
        )

        # Prepare portal layout values
        values = self._prepare_portal_layout_values()
        values.update({
            "assignments": assignments,
            "page_name": "vendor_assignments",
            "pager": pager,
            "default_url": "/my/vendor-assignments",
            "searchbar_sortings": searchbar_sortings,
            "sortby": sortby,
            "searchbar_filters": searchbar_filters,
            "filterby": filterby,
            # Pass message/error from query params to template
            "success_message": kw.get("message"),
            "error_message": kw.get("error"),
        })

        return request.render("ptt_business_core.portal_vendor_assignment_list", values)

    # === ASSIGNMENT DETAIL VIEW ===
    @http.route(
        ["/my/vendor-assignments/<int:assignment_id>"],
        type="http",
        auth="user",
        website=True,
    )
    def portal_vendor_assignment_detail(self, assignment_id, access_token=None, **kw):
        """Display details of a specific vendor assignment.
        
        Uses standard _document_check_access for security and
        _get_page_view_values for proper chatter setup.
        """
        try:
            # Use the standard CustomerPortal._document_check_access (inherited)
            # This returns a SUDO version of the record after access validation
            assignment_sudo = self._document_check_access(
                "ptt.project.vendor.assignment",
                assignment_id,
                access_token=access_token,
            )
        except (AccessError, MissingError):
            return request.redirect("/my/vendor-assignments")

        # Get attachments for this assignment (use sudo to ensure we can see them)
        attachments = request.env["ir.attachment"].sudo().search([
            ("res_model", "=", "ptt.project.vendor.assignment"),
            ("res_id", "=", assignment_id),
        ])

        # Prepare base values with portal layout
        values = self._prepare_portal_layout_values()
        
        # Use _get_page_view_values for proper chatter setup (token, hash, pid)
        values = self._get_page_view_values(
            assignment_sudo,
            access_token,
            values,
            'my_vendor_assignments_history',
            False,  # no_breadcrumbs
        )
        
        # Add our custom values
        values.update({
            "assignment": assignment_sudo,
            "page_name": "vendor_assignment_detail",
            "attachments": attachments,
            # Pass message/error from query params to template
            "success_message": kw.get("message"),
            "error_message": kw.get("error"),
        })

        return request.render("ptt_business_core.portal_vendor_assignment_detail", values)

    # === ACCEPT ASSIGNMENT ===
    @http.route(
        ["/my/vendor-assignments/<int:assignment_id>/accept"],
        type="http",
        auth="user",
        website=True,
        methods=["POST"],
    )
    def portal_vendor_assignment_accept(self, assignment_id, access_token=None, **kw):
        """Accept a vendor assignment."""
        try:
            assignment_sudo = self._document_check_access(
                "ptt.project.vendor.assignment",
                assignment_id,
                access_token=access_token,
            )
        except (AccessError, MissingError):
            return request.redirect("/my/vendor-assignments")

        try:
            # action_vendor_accept validates vendor ownership internally
            assignment_sudo.action_vendor_accept()
        except (UserError, AccessError) as e:
            # URL encode the error message
            error_msg = str(e.args[0]) if e.args else str(e)
            return request.redirect(
                f"/my/vendor-assignments/{assignment_id}?error={error_msg}"
            )

        return request.redirect(
            f"/my/vendor-assignments/{assignment_id}?message=accepted"
        )

    # === DECLINE ASSIGNMENT ===
    @http.route(
        ["/my/vendor-assignments/<int:assignment_id>/decline"],
        type="http",
        auth="user",
        website=True,
        methods=["POST"],
    )
    def portal_vendor_assignment_decline(self, assignment_id, access_token=None, **kw):
        """Decline a vendor assignment."""
        try:
            assignment_sudo = self._document_check_access(
                "ptt.project.vendor.assignment",
                assignment_id,
                access_token=access_token,
            )
        except (AccessError, MissingError):
            return request.redirect("/my/vendor-assignments")

        try:
            assignment_sudo.action_vendor_decline()
        except (UserError, AccessError) as e:
            error_msg = str(e.args[0]) if e.args else str(e)
            return request.redirect(
                f"/my/vendor-assignments/{assignment_id}?error={error_msg}"
            )

        return request.redirect(
            f"/my/vendor-assignments/{assignment_id}?message=declined"
        )

    # === FILE UPLOAD ===
    @http.route(
        ["/my/vendor-assignments/<int:assignment_id>/upload"],
        type="http",
        auth="user",
        website=True,
        methods=["POST"],
    )
    def portal_vendor_assignment_upload(self, assignment_id, access_token=None, **kw):
        """Upload a file attachment to a vendor assignment.
        
        Includes security validations:
        - File extension whitelist
        - File size limit
        - Access validation via _document_check_access
        """
        try:
            assignment_sudo = self._document_check_access(
                "ptt.project.vendor.assignment",
                assignment_id,
                access_token=access_token,
            )
        except (AccessError, MissingError):
            return request.redirect("/my/vendor-assignments")

        # Get uploaded file
        uploaded_file = kw.get("attachment")
        if not uploaded_file:
            return request.redirect(
                f"/my/vendor-assignments/{assignment_id}?error=No file selected"
            )

        # Security: Validate file extension
        filename = uploaded_file.filename
        file_ext = '.' + filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        if file_ext not in ALLOWED_EXTENSIONS:
            return request.redirect(
                f"/my/vendor-assignments/{assignment_id}?error=File type not allowed. Please upload PDF, DOC, XLS, or image files."
            )

        # Read and validate file size
        file_content = uploaded_file.read()
        if len(file_content) > MAX_FILE_SIZE:
            return request.redirect(
                f"/my/vendor-assignments/{assignment_id}?error=File too large. Maximum size is 10 MB."
            )

        # Create attachment - datas must be base64 encoded string
        attachment_data = {
            "name": filename,
            "datas": base64.b64encode(file_content).decode('utf-8'),
            "res_model": "ptt.project.vendor.assignment",
            "res_id": assignment_id,
            "mimetype": mimetypes.guess_type(filename)[0] or 'application/octet-stream',
        }
        # Use sudo to create attachment (portal users may not have create rights on ir.attachment)
        request.env["ir.attachment"].sudo().create(attachment_data)

        # Post a message about the upload
        assignment_sudo.message_post(
            body=_("File uploaded by vendor: %s", filename),
            message_type="comment",
            subtype_xmlid="mail.mt_comment",
        )

        return request.redirect(
            f"/my/vendor-assignments/{assignment_id}?message=file_uploaded"
        )

    # === POST MESSAGE ===
    @http.route(
        ["/my/vendor-assignments/<int:assignment_id>/message"],
        type="http",
        auth="user",
        website=True,
        methods=["POST"],
    )
    def portal_vendor_assignment_message(self, assignment_id, access_token=None, **kw):
        """Post a message to the assignment chatter."""
        try:
            assignment_sudo = self._document_check_access(
                "ptt.project.vendor.assignment",
                assignment_id,
                access_token=access_token,
            )
        except (AccessError, MissingError):
            return request.redirect("/my/vendor-assignments")

        message_body = kw.get("message", "").strip()
        if message_body:
            # Post message from the vendor
            assignment_sudo.message_post(
                body=message_body,
                message_type="comment",
                subtype_xmlid="mail.mt_comment",
            )

        return request.redirect(f"/my/vendor-assignments/{assignment_id}")

    # === DOCUMENT LIST VIEW ===
    @http.route(
        ["/my/vendor-documents", "/my/vendor-documents/page/<int:page>"],
        type="http",
        auth="user",
        website=True,
    )
    def portal_vendor_documents(self, page=1, **kw):
        """Display list of vendor documents for the current portal user."""
        VendorDocument = request.env["ptt.vendor.document"]
        partner = request.env.user.partner_id

        domain = [("vendor_id", "=", partner.id)]

        document_count = VendorDocument.search_count(domain)

        pager = portal_pager(
            url="/my/vendor-documents",
            total=document_count,
            page=page,
            step=10,
        )

        documents = VendorDocument.search(
            domain,
            order="document_type_id, validity desc",
            limit=10,
            offset=pager["offset"],
        )

        # Get document types for upload form
        document_types = request.env["ptt.document.type"].sudo().search([
            ("active", "=", True)
        ], order="sequence, name")

        values = self._prepare_portal_layout_values()
        values.update({
            "documents": documents,
            "document_types": document_types,
            "page_name": "vendor_documents",
            "pager": pager,
            "default_url": "/my/vendor-documents",
            "message": kw.get("message"),
            "error": kw.get("error"),
        })

        return request.render("ptt_business_core.portal_vendor_document_list", values)

    # === DOCUMENT UPLOAD ===
    @http.route(
        ["/my/vendor-documents/upload"],
        type="http",
        auth="user",
        website=True,
        methods=["POST"],
    )
    def portal_vendor_document_upload(self, **kw):
        """Upload a new vendor document."""
        partner = request.env.user.partner_id
        vendor = partner if partner.x_is_vendor else False

        if not vendor:
            return request.redirect("/my/vendor-documents?error=Not a vendor")

        uploaded_file = kw.get("attachment")
        document_type_id = kw.get("document_type_id")
        validity = kw.get("validity", "").strip()

        if not uploaded_file or not document_type_id:
            return request.redirect("/my/vendor-documents?error=Missing file or document type")

        # Security: Validate file extension
        filename = uploaded_file.filename
        file_ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if file_ext not in ALLOWED_EXTENSIONS:
            return request.redirect(
                "/my/vendor-documents?error=File type not allowed. Please upload PDF, DOC, XLS, or image files."
            )

        # Read and validate file size
        file_content = uploaded_file.read()
        if len(file_content) > MAX_FILE_SIZE:
            return request.redirect(
                "/my/vendor-documents?error=File too large. Maximum size is 10 MB."
            )

        # Parse validity date
        validity_date = False
        if validity:
            try:
                validity_date = fields.Date.from_string(validity)
            except Exception:
                pass

        # Create document
        doc_vals = {
            "vendor_id": vendor.id,
            "document_type_id": int(document_type_id),
            "attached_document": base64.b64encode(file_content).decode("utf-8"),
            "document_filename": filename,
            "validity": validity_date,
            "upload_date": fields.Datetime.now(),
        }

        request.env["ptt.vendor.document"].sudo().create(doc_vals)

        return request.redirect("/my/vendor-documents?message=Document uploaded successfully")

    # === DOCUMENT DOWNLOAD ===
    @http.route(
        ["/my/vendor-documents/<int:document_id>/download"],
        type="http",
        auth="user",
        website=True,
    )
    def portal_vendor_document_download(self, document_id, **kw):
        """Download a vendor document."""
        partner = request.env.user.partner_id

        document = request.env["ptt.vendor.document"].sudo().browse(document_id)

        if document.vendor_id.id != partner.id:
            return request.redirect("/my/vendor-documents?error=Access denied")

        if not document.attached_document:
            return request.redirect("/my/vendor-documents?error=Document not found")

        filename = document.document_filename or f"document_{document_id}"

        # Use standard Odoo web/content route for file download
        return request.redirect(
            f"/web/content/ptt.vendor.document/{document_id}/attached_document/{filename}?download=true"
        )