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
"""

import base64
from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.exceptions import AccessError, MissingError
from odoo.osv.expression import AND


class VendorPortal(CustomerPortal):
    """Portal controller for vendor assignment management."""

    # === PORTAL HOME COUNTERS ===
    def _prepare_home_portal_values(self, counters):
        """Add vendor assignment count to portal home page."""
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
        domain = AND([
            [("vendor_id", "=", partner.id)],
            searchbar_filters[filterby]["domain"],
        ])

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

        values = {
            "assignments": assignments,
            "page_name": "vendor_assignments",
            "pager": pager,
            "default_url": "/my/vendor-assignments",
            "searchbar_sortings": searchbar_sortings,
            "sortby": sortby,
            "searchbar_filters": searchbar_filters,
            "filterby": filterby,
        }

        return request.render("ptt_business_core.portal_vendor_assignment_list", values)

    # === ASSIGNMENT DETAIL VIEW ===
    @http.route(
        ["/my/vendor-assignments/<int:assignment_id>"],
        type="http",
        auth="user",
        website=True,
    )
    def portal_vendor_assignment_detail(self, assignment_id, **kw):
        """Display details of a specific vendor assignment."""
        try:
            assignment = self._document_check_access(
                "ptt.project.vendor.assignment",
                assignment_id,
            )
        except (AccessError, MissingError):
            return request.redirect("/my/vendor-assignments")

        # Get attachments for this assignment
        attachments = request.env["ir.attachment"].search([
            ("res_model", "=", "ptt.project.vendor.assignment"),
            ("res_id", "=", assignment_id),
        ])

        values = {
            "assignment": assignment,
            "page_name": "vendor_assignment_detail",
            "attachments": attachments,
        }

        return request.render("ptt_business_core.portal_vendor_assignment_detail", values)

    # === ACCEPT ASSIGNMENT ===
    @http.route(
        ["/my/vendor-assignments/<int:assignment_id>/accept"],
        type="http",
        auth="user",
        website=True,
        methods=["POST"],
    )
    def portal_vendor_assignment_accept(self, assignment_id, **kw):
        """Accept a vendor assignment."""
        try:
            assignment = self._document_check_access(
                "ptt.project.vendor.assignment",
                assignment_id,
            )
        except (AccessError, MissingError):
            return request.redirect("/my/vendor-assignments")

        try:
            assignment.action_vendor_accept()
        except Exception as e:
            # Log error and redirect with message
            return request.redirect(
                f"/my/vendor-assignments/{assignment_id}?error={str(e)}"
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
    def portal_vendor_assignment_decline(self, assignment_id, **kw):
        """Decline a vendor assignment."""
        try:
            assignment = self._document_check_access(
                "ptt.project.vendor.assignment",
                assignment_id,
            )
        except (AccessError, MissingError):
            return request.redirect("/my/vendor-assignments")

        try:
            assignment.action_vendor_decline()
        except Exception as e:
            return request.redirect(
                f"/my/vendor-assignments/{assignment_id}?error={str(e)}"
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
    def portal_vendor_assignment_upload(self, assignment_id, **kw):
        """Upload a file attachment to a vendor assignment."""
        try:
            assignment = self._document_check_access(
                "ptt.project.vendor.assignment",
                assignment_id,
            )
        except (AccessError, MissingError):
            return request.redirect("/my/vendor-assignments")

        # Get uploaded file
        uploaded_file = kw.get("attachment")
        if uploaded_file:
            # Create attachment - datas must be base64 encoded
            file_content = uploaded_file.read()
            attachment_data = {
                "name": uploaded_file.filename,
                "datas": base64.b64encode(file_content),
                "res_model": "ptt.project.vendor.assignment",
                "res_id": assignment_id,
            }
            # Use sudo to create attachment (portal users may not have create rights on ir.attachment)
            request.env["ir.attachment"].sudo().create(attachment_data)

            # Post a message about the upload
            assignment.message_post(
                body=_("File uploaded: %s", uploaded_file.filename),
                message_type="comment",
            )

        return request.redirect(f"/my/vendor-assignments/{assignment_id}")

    # === POST MESSAGE ===
    @http.route(
        ["/my/vendor-assignments/<int:assignment_id>/message"],
        type="http",
        auth="user",
        website=True,
        methods=["POST"],
    )
    def portal_vendor_assignment_message(self, assignment_id, **kw):
        """Post a message to the assignment chatter."""
        try:
            assignment = self._document_check_access(
                "ptt.project.vendor.assignment",
                assignment_id,
            )
        except (AccessError, MissingError):
            return request.redirect("/my/vendor-assignments")

        message_body = kw.get("message", "").strip()
        if message_body:
            assignment.message_post(
                body=message_body,
                message_type="comment",
            )

        return request.redirect(f"/my/vendor-assignments/{assignment_id}")

    # === HELPER METHODS ===
    def _document_check_access(self, model_name, document_id, access_token=None):
        """Check if current user has access to the document."""
        document = request.env[model_name].browse(document_id)
        if not document.exists():
            raise MissingError(_("This document does not exist."))

        # Check if user can access this document
        try:
            document.check_access_rights("read")
            document.check_access_rule("read")
        except AccessError:
            raise AccessError(_("You do not have access to this document."))

        return document
