"""
Extend ptt.project.vendor.assignment for vendor portal functionality.

SIMPLIFIED: Adds portal-related fields to existing model.
Reference: https://www.odoo.com/documentation/19.0/developer/reference/backend/orm.html
"""
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ProjectVendorAssignment(models.Model):
    """Extend ptt.project.vendor.assignment with vendor work order fields."""
    
    _inherit = 'ptt.project.vendor.assignment'
    
    # === VENDOR RESPONSE FIELDS ===
    vendor_signature = fields.Binary(
        string="Vendor Signature",
        attachment=True,
        help="Digital signature from vendor accepting work order",
    )
    vendor_signature_date = fields.Datetime(
        string="Signature Date",
        readonly=True,
        help="Date/time when vendor signed acceptance",
    )
    vendor_decline_reason = fields.Text(
        string="Decline Reason",
        readonly=True,
        help="Reason provided by vendor for declining work order",
    )
    
    # === PORTAL ACCESS ===
    access_token = fields.Char(
        string="Access Token",
        copy=False,
        help="Token for portal access",
    )
    access_token_expiry = fields.Datetime(
        string="Token Expiry",
        copy=False,
        help="Date/time when the access token expires (default: 30 days from generation)",
    )
    
    def _get_access_token(self):
        """Generate access token for portal link with expiration.
        
        Tokens expire after 30 days for security. Expired tokens are regenerated.
        """
        import uuid
        from datetime import timedelta
        
        now = fields.Datetime.now()
        
        # Check if token exists and is not expired
        if self.access_token and self.access_token_expiry:
            if self.access_token_expiry > now:
                return self.access_token
            # Token expired - regenerate
        
        # Generate new token with 30-day expiry
        self.access_token = str(uuid.uuid4())
        self.access_token_expiry = now + timedelta(days=30)
        return self.access_token
    
    def _is_token_valid(self, token):
        """Validate access token including expiry check.
        
        Returns True if token matches and is not expired.
        """
        if not self.access_token or self.access_token != token:
            return False
        
        # Check expiry if set
        if self.access_token_expiry:
            if self.access_token_expiry < fields.Datetime.now():
                return False
        
        return True
    
    # === ACTIONS ===
    
    def action_send_work_order(self):
        """Send work order to vendor via email.
        
        Called from the VENDORS tab "Send WO" button on project form.
        """
        self.ensure_one()
        
        if not self.vendor_id:
            raise UserError(_("Please assign a vendor before sending work order."))
        
        if not self.vendor_id.email:
            raise UserError(_("Vendor %s has no email address.") % self.vendor_id.name)
        
        # Update status to sent (use existing ptt_status field)
        self.ptt_status = 'pending'
        
        # Generate access token
        self._get_access_token()
        
        # Send email
        template = self.env.ref('ptt_vendor_management.email_template_vendor_work_order', raise_if_not_found=False)
        if template:
            template.send_mail(self.id, force_send=True)
        
        self.message_post(
            body=_("Work order sent to %s") % self.vendor_id.name,
            message_type='notification',
        )
        
        return True
    
    def action_vendor_accept(self, signature=None):
        """Vendor accepts work order (called from portal).
        
        Args:
            signature: Optional base64 signature image
        """
        self.ensure_one()
        
        self.write({
            'ptt_status': 'confirmed',
            'vendor_signature': signature,
            'vendor_signature_date': fields.Datetime.now(),
            'ptt_confirmed_date': fields.Date.today(),
        })
        
        # Get service type display name (defensive - selection may not exist)
        service_type_label = self.service_type
        if 'service_type' in self._fields and hasattr(self._fields['service_type'], 'selection'):
            selection = self._fields['service_type'].selection
            if callable(selection):
                try:
                    selection = selection(self)
                except Exception:
                    selection = []
            service_type_label = dict(selection).get(self.service_type, self.service_type)
        
        # Notify project manager (defensive - project_id may be unset)
        if self.project_id:
            self.project_id.message_post(
                body=_("✅ %s accepted %s assignment for %s") % (
                    self.vendor_id.name if self.vendor_id else _("Unknown"),
                    service_type_label,
                    self.project_id.ptt_event_date or 'TBD'
                ),
                subject=_("Vendor Accepted: %s") % service_type_label,
                message_type='notification',
            )
        
        return True
    
    def action_vendor_decline(self, reason=None):
        """Vendor declines work order (called from portal).
        
        Args:
            reason: Optional text reason for declining
        """
        self.ensure_one()
        
        self.write({
            'ptt_status': 'cancelled',
            'vendor_decline_reason': reason or _("No reason provided"),
        })
        
        # Get service type display name (defensive - selection may not exist)
        service_type_label = self.service_type
        if 'service_type' in self._fields and hasattr(self._fields['service_type'], 'selection'):
            selection = self._fields['service_type'].selection
            if callable(selection):
                try:
                    selection = selection(self)
                except Exception:
                    selection = []
            service_type_label = dict(selection).get(self.service_type, self.service_type)
        
        # URGENT notification to project manager (defensive - project_id may be unset)
        if self.project_id:
            self.project_id.message_post(
                body=_("❌ URGENT: %s declined %s assignment!<br/>Reason: %s") % (
                    self.vendor_id.name if self.vendor_id else _("Unknown"),
                    service_type_label,
                    reason or _("Not specified")
                ),
                subject=_("URGENT: Vendor Declined - %s") % service_type_label,
                message_type='notification',
            )
        
        return True
    
    def action_resend_work_order(self):
        """Resend work order email to vendor."""
        self.ensure_one()
        
        template = self.env.ref('ptt_vendor_management.email_template_vendor_work_order', raise_if_not_found=False)
        if template:
            template.send_mail(self.id, force_send=True)
        
        return True
    
    def action_mark_completed(self):
        """Mark work order as completed (after event)."""
        self.ensure_one()
        self.ptt_status = 'completed'
        return True
