"""
Extend ptt.project.vendor.assignment for vendor portal functionality.

SIMPLIFIED: Uses portal.mixin for native portal support.
Reference: https://www.odoo.com/documentation/19.0/developer/reference/backend/orm.html
"""
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ProjectVendorAssignment(models.Model):
    """Extend ptt.project.vendor.assignment with portal.mixin for vendor work order portal."""
    
    _inherit = ['ptt.project.vendor.assignment', 'portal.mixin', 'mail.thread']  # Extend existing model + add portal.mixin (mail.thread already in base, but explicit for clarity)
    
    # === PORTAL STATE TRACKING ===
    # Replaces ptt_status from base model with portal-aware state
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Work Order Sent'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], string='Portal Status', default='draft', tracking=True, copy=False,
       help="Work order portal status: Draft → Sent → Accepted/Declined → Completed")
    
    # === VENDOR RESPONSE ===
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
    
    # === PORTAL.MIXIN REQUIRED METHODS ===
    
    @api.depends()
    def _compute_access_url(self):
        """Required by portal.mixin - returns portal URL for each record.
        
        Reference: https://www.odoo.com/documentation/19.0/developer/reference/backend/orm.html#portal-mixin
        Note: Uses plural '/my/work-orders/' to match controller list route.
        """
        for rec in self:
            rec.access_url = f'/my/work-orders/{rec.id}'
    
    def _get_report_base_filename(self):
        """Optional - for PDF generation."""
        return f'WorkOrder-{self.id}'
    
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
        
        # Update state
        self.state = 'sent'
        
        # Send email - portal.mixin provides access_token automatically
        template = self.env.ref('ptt_vendor_management.email_template_vendor_work_order', raise_if_not_found=False)
        if template:
            self.message_post_with_template(
                template.id,
                composition_mode='comment',
                email_layout_xmlid='mail.mail_notification_light',
            )
        else:
            # Fallback: just post a message with portal URL
            # portal.mixin provides _get_share_url() method which includes access_token
            base_url = self.get_base_url()
            portal_url = base_url + self._get_share_url()
            self.message_post(
                body=_("Work order sent to %s. Portal link: %s") % (
                    self.vendor_id.name,
                    portal_url,
                ),
                message_type='notification',
            )
        
        return True
    
    def action_vendor_accept(self, signature=None):
        """Vendor accepts work order (called from portal).
        
        Args:
            signature: Optional base64 signature image
        """
        self.ensure_one()
        
        if self.state != 'sent':
            raise UserError(_("Only pending work orders can be accepted."))
        
        self.write({
            'state': 'accepted',
            'vendor_signature': signature,
            'vendor_signature_date': fields.Datetime.now(),
        })
        
        # Get service type display name
        service_type_label = dict(self._fields['service_type'].selection).get(
            self.service_type, self.service_type
        )
        
        # Notify project manager
        self.project_id.message_post(
            body=_("✅ %s accepted %s assignment for %s") % (
                self.vendor_id.name,
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
        
        if self.state != 'sent':
            raise UserError(_("Only pending work orders can be declined."))
        
        self.write({
            'state': 'declined',
            'vendor_decline_reason': reason or _("No reason provided"),
        })
        
        # Get service type display name
        service_type_label = dict(self._fields['service_type'].selection).get(
            self.service_type, self.service_type
        )
        
        # URGENT notification to project manager
        partner_ids = []
        if self.project_id.user_id and self.project_id.user_id.partner_id:
            partner_ids = self.project_id.user_id.partner_id.ids
        
        self.project_id.message_post(
            body=_("❌ URGENT: %s declined %s assignment!<br/>Reason: %s") % (
                self.vendor_id.name,
                service_type_label,
                reason or _("Not specified")
            ),
            subject=_("URGENT: Vendor Declined - %s") % service_type_label,
            message_type='notification',
            partner_ids=partner_ids,
        )
        
        return True
    
    def action_resend_work_order(self):
        """Resend work order email to vendor."""
        self.ensure_one()
        
        if self.state not in ('sent', 'declined'):
            raise UserError(_("Can only resend sent or declined work orders."))
        
        template = self.env.ref('ptt_vendor_management.email_template_vendor_work_order', raise_if_not_found=False)
        if template:
            self.message_post_with_template(
                template.id,
                composition_mode='comment',
                email_layout_xmlid='mail.mail_notification_light',
            )
        
        return True
    
    def action_mark_completed(self):
        """Mark work order as completed (after event)."""
        self.ensure_one()
        
        if self.state != 'accepted':
            raise UserError(_("Only accepted work orders can be marked completed."))
        
        self.state = 'completed'
        return True
    
    def action_cancel(self):
        """Cancel work order."""
        self.ensure_one()
        
        if self.state == 'completed':
            raise UserError(_("Cannot cancel completed work orders."))
        
        self.state = 'cancelled'
        return True
