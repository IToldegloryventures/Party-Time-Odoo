import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    """Inherit purchase.order to validate vendor documents before confirmation."""
    _inherit = "purchase.order"

    @api.model
    def _is_vendor_management_installed(self):
        """Check if ptt_vendor_management module is installed.
        
        More reliable than checking if model exists in registry.
        """
        IrModule = self.env['ir.module.module'].sudo()
        module = IrModule.search([
            ('name', '=', 'ptt_vendor_management'),
            ('state', '=', 'installed'),
        ], limit=1)
        return bool(module)

    @api.model
    def _check_vendor_documents(self, vendor):
        """Check if vendor has valid required documents.
        
        Returns: (is_valid, error_message)
        """
        if not vendor or vendor.supplier_rank == 0:
            return True, None
        
        # Defensive check - ensure ptt.document.type model exists
        if 'ptt.document.type' not in self.env:
            return True, None
        
        # Get required document types
        required_doc_types = self.env["ptt.document.type"].search([
            ("required", "=", True),
            ("active", "=", True),
        ])
        
        if not required_doc_types:
            return True, None
        
        # Check each required document
        missing_docs = []
        expired_docs = []
        
        for doc_type in required_doc_types:
            doc = vendor.ptt_vendor_document_ids.filtered(
                lambda d: d.document_type_id.id == doc_type.id
            )
            
            if not doc:
                missing_docs.append(doc_type.name)
            elif doc.status == "expired":
                expired_docs.append(doc_type.name)
        
        if missing_docs or expired_docs:
            error_parts = []
            if missing_docs:
                error_parts.append(_("Missing required documents: %s") % ", ".join(missing_docs))
            if expired_docs:
                error_parts.append(_("Expired documents: %s") % ", ".join(expired_docs))
            
            return False, "\n".join(error_parts)
        
        return True, None

    def button_confirm(self):
        """Override to check vendor documents before confirming PO.
        
        Note: Document validation only works if ptt_vendor_management is installed.
        If not installed, PO confirmation proceeds without validation.
        """
        # Only validate if ptt_vendor_management is installed AND model exists
        try:
            if 'ptt.document.type' in self.env and self._is_vendor_management_installed():
                for order in self:
                    if order.partner_id:
                        is_valid, error_msg = self._check_vendor_documents(order.partner_id)
                        if not is_valid:
                            raise UserError(
                                _("Cannot confirm Purchase Order: Vendor document compliance issue.\n\n%s")
                                % error_msg
                            )
        except Exception as e:
            # Log but don't block PO confirmation if vendor check fails
            _logger.warning("Vendor document check failed: %s. Proceeding with PO confirmation.", e)
        
        return super().button_confirm()
