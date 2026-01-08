# -*- coding: utf-8 -*-
"""
Vendor Intake Portal Controller
================================
Public "Work with Us" / "Join Our Team" vendor application form.
No authentication required - vendors can apply directly.

Route: /vendor/apply (public)
"""

import base64
import logging
import re
from odoo import http, fields, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# Allowed file extensions for uploads (security)
ALLOWED_EXTENSIONS = {
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.png', '.jpg', '.jpeg',
    '.gif', '.txt', '.csv', '.zip'
}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

# Service types selection (same as in models)
SERVICE_TYPES = [
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
]


class VendorIntakePortal(CustomerPortal):
    """Public vendor intake form controller."""

    @http.route(
        ["/vendor/apply"],
        type="http",
        auth="public",
        website=True,
        csrf=False,
    )
    def portal_vendor_apply(self, **kw):
        """Display vendor application form or handle submission."""
        if request.httprequest.method == "POST":
            return self._handle_application_submission(**kw)

        # Get document types for the form
        document_types = request.env["ptt.document.type"].sudo().search([
            ("active", "=", True)
        ], order="sequence, name")

        values = {
            "document_types": document_types,
            "service_types": SERVICE_TYPES,
            "page_name": "vendor_application",
            "error": kw.get("error"),
        }

        return request.render("ptt_business_core.portal_vendor_application", values)

    def _validate_documents(self, kw, document_types):
        """Validate required documents and expiry dates."""
        missing_documents = []
        missing_expiry_dates = []

        for doc_type in document_types:
            document_field_name = f"{doc_type.code}_document"
            uploaded_file = request.httprequest.files.get(document_field_name)
            is_uploaded = (
                uploaded_file
                and hasattr(uploaded_file, "filename")
                and uploaded_file.filename
                and uploaded_file.filename.strip()
            )

            if doc_type.required and not is_uploaded:
                missing_documents.append(doc_type.name)

            if doc_type.has_expiry and is_uploaded:
                validity_field_name = f"{doc_type.code}_validity"
                validity_date = kw.get(validity_field_name, "").strip()
                if not validity_date:
                    missing_expiry_dates.append(doc_type.name)

        error_messages = []
        if missing_documents:
            error_messages.append(
                _("The following documents are missing: %s") % ", ".join(missing_documents)
            )
        if missing_expiry_dates:
            error_messages.append(
                _("The following documents require an expiry date: %s")
                % ", ".join(missing_expiry_dates)
            )

        if error_messages:
            raise UserError(" ".join(error_messages))

    def _handle_application_submission(self, **kw):
        """Handle vendor application form submission."""
        try:
            # Validate required fields
            required_fields = [
                ("name", _("Company Name")),
                ("email", _("Company Email")),
                ("phone", _("Company Phone")),
            ]

            missing_fields = []
            for field, label in required_fields:
                field_value = kw.get(field)
                if not field_value or not str(field_value).strip():
                    missing_fields.append(label)

            if missing_fields:
                raise UserError(
                    _("The following fields are required: %s") % ", ".join(missing_fields)
                )

            # Validate email format
            email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            if not re.match(email_pattern, kw.get("email", "")):
                raise UserError(_("Please enter a valid company email address."))

            # Get service types (can be multiple)
            service_types = kw.get("service_types", [])
            if isinstance(service_types, str):
                service_types = [service_types]
            elif not isinstance(service_types, list):
                service_types = []

            if not service_types:
                raise UserError(_("Please select at least one service type."))

            # Get document types
            document_types = request.env["ptt.document.type"].sudo().search([
                ("active", "=", True)
            ])

            # Validate documents
            self._validate_documents(kw, document_types)

            # Create vendor partner
            vendor_vals = {
                "name": kw.get("name", "").strip(),
                "email": kw.get("email", "").strip(),
                "phone": kw.get("phone", "").strip(),
                "street": kw.get("street", "").strip() or False,
                "street2": kw.get("street2", "").strip() or False,
                "city": kw.get("city", "").strip() or False,
                "state_id": int(kw.get("state_id", 0)) if kw.get("state_id") else False,
                "zip": kw.get("zip", "").strip() or False,
                "country_id": int(kw.get("country_id", 0)) if kw.get("country_id") else False,
                "website": kw.get("website", "").strip() or False,
                "x_is_vendor": True,
                "x_vendor_status": "pending_review",
                "x_vendor_service_types": service_types[0] if service_types else False,
                "x_vendor_tier": "unqualified",
                "is_company": True,
                "supplier_rank": 5,
            }

            vendor = request.env["res.partner"].sudo().create(vendor_vals)

            # Create vendor service pricing entries (without prices - will be filled later)
            for service_type in service_types:
                request.env["ptt.vendor.service"].sudo().create({
                    "vendor_id": vendor.id,
                    "service_type": service_type,
                })

            # Process document uploads
            for doc_type in document_types:
                document_field_name = f"{doc_type.code}_document"
                uploaded_file = request.httprequest.files.get(document_field_name)

                if uploaded_file and hasattr(uploaded_file, "filename") and uploaded_file.filename:
                    try:
                        uploaded_file.seek(0)
                        file_content = uploaded_file.read()

                        if len(file_content) > MAX_FILE_SIZE:
                            continue  # Skip oversized files

                        # Validate file extension
                        filename = uploaded_file.filename
                        file_ext = (
                            "." + filename.rsplit(".", 1)[-1].lower()
                            if "." in filename
                            else ""
                        )
                        if file_ext not in ALLOWED_EXTENSIONS:
                            continue  # Skip invalid file types

                        validity_date = kw.get(f"{doc_type.code}_validity", "").strip()
                        validity = False
                        if validity_date:
                            try:
                                validity = fields.Date.from_string(validity_date)
                            except Exception:
                                pass

                        file_content_b64 = base64.b64encode(file_content)

                        doc_vals = {
                            "vendor_id": vendor.id,
                            "document_type_id": doc_type.id,
                            "attached_document": file_content_b64,
                            "document_filename": filename,
                            "validity": validity,
                            "upload_date": fields.Datetime.now(),
                        }

                        request.env["ptt.vendor.document"].sudo().create(doc_vals)
                    except Exception as e:
                        _logger.error(
                            "Error creating document record for %s (%s): %s",
                            doc_type.name,
                            doc_type.code,
                            str(e),
                        )

            # Post success message
            vendor.message_post(
                body=_("Vendor application submitted via portal form."),
                message_type="notification",
            )

            # Redirect to thank you page
            return request.render("ptt_business_core.portal_vendor_application_thankyou", {
                "vendor": vendor,
            })

        except UserError as e:
            # Re-render form with error
            document_types = request.env["ptt.document.type"].sudo().search([
                ("active", "=", True)
            ], order="sequence, name")

            return request.render("ptt_business_core.portal_vendor_application", {
                "document_types": document_types,
                "service_types": SERVICE_TYPES,
                "page_name": "vendor_application",
                "error": str(e),
            })
        except Exception as e:
            _logger.error("Error creating vendor application: %s", str(e))
            return request.render("ptt_business_core.portal_vendor_application", {
                "document_types": request.env["ptt.document.type"].sudo().search([
                    ("active", "=", True)
                ], order="sequence, name"),
                "service_types": SERVICE_TYPES,
                "page_name": "vendor_application",
                "error": _("An error occurred. Please try again or contact support."),
            })
