"""
Extend ptt.project.vendor.assignment for vendor portal functionality.

SIMPLIFIED: Adds portal-related fields to existing model.
Reference: https://www.odoo.com/documentation/19.0/developer/reference/backend/orm.html
"""
import uuid

from datetime import timedelta

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
    
    # === PORTAL-SPECIFIC EVENT DETAILS ===
    ptt_arrival_time = fields.Char(
        string="Arrival Time",
        help="Expected arrival/setup time for vendor",
    )
    
    # === VENDOR TASKS ===
    vendor_task_ids = fields.One2many(
        "ptt.vendor.task",
        "assignment_id",
        string="Vendor Task Lines",
        help="Tasks assigned to this vendor for this work order",
    )
    
    vendor_task_count = fields.Integer(
        string="Vendor Tasks",
        compute="_compute_vendor_task_count",
    )

    vendor_pricing_hint = fields.Char(
        string="Typical Rate",
        compute="_compute_vendor_pricing_hint",
        help="Suggested vendor rate from the vendor pricing table",
    )

    last_reminder_date = fields.Datetime(
        string="Last Reminder Sent",
        readonly=True,
        help="Last time a pending work order reminder was sent",
    )
    
    # === RELATED FIELDS FOR PORTAL ===
    event_date = fields.Date(
        string="Event Date",
        related="project_id.ptt_event_date",
        store=True,
        readonly=True,
    )
    
    @api.depends("vendor_task_ids")
    def _compute_vendor_task_count(self):
        for record in self:
            record.vendor_task_count = len(record.vendor_task_ids)

    @api.depends("vendor_id", "service_type")
    def _compute_vendor_pricing_hint(self):
        """Compute pricing hint from vendor's service pricing records.
        
        Looks up the vendor's pricing for the service type by matching
        the service_type selection code to product names/codes.
        """
        Pricing = self.env["ptt.vendor.service.pricing"]
        Product = self.env["product.template"]
        for record in self:
            record.vendor_pricing_hint = False
            if not record.vendor_id or not record.service_type:
                continue
            
            # Get the display label for this service type
            label = dict(record._fields["service_type"].selection).get(
                record.service_type, record.service_type
            )
            
            # Find matching product by name (case-insensitive)
            product = Product.search([
                ("type", "=", "service"),
                ("name", "ilike", label),
            ], limit=1)
            
            if not product:
                continue
            
            # Find pricing for this vendor + product
            pricing = Pricing.search([
                ("vendor_id", "=", record.vendor_id.id),
                ("service_product_id", "=", product.id),
            ], limit=1)
            record.vendor_pricing_hint = pricing.price_detail if pricing else False
    
    def _get_access_token(self):
        """Generate access token for portal link."""
        if not self.access_token:
            self.access_token = str(uuid.uuid4())
        return self.access_token
    
    # === ACTIONS ===
    
    def action_send_work_order(self):
        """Send work order to vendor via email.
        
        Called from the VENDORS tab "Send WO" button on project form.
        Subscribes project manager and responsible user as followers for notifications.
        """
        self.ensure_one()
        
        if not self.vendor_id:
            raise UserError(_("Please assign a vendor before sending work order."))
        
        if not self.vendor_id.email:
            raise UserError(_("Vendor %s has no email address.") % self.vendor_id.name)
        
        # Update status to sent (work order sent, awaiting vendor response)
        self.status = 'sent'
        
        # Generate access token
        self._get_access_token()
        
        # Subscribe internal team as followers for vendor message notifications
        followers_to_add = []
        # Add project manager
        if self.project_id.user_id and self.project_id.user_id.partner_id:
            followers_to_add.append(self.project_id.user_id.partner_id.id)
        # Add current user (person sending work order)
        if self.env.user.partner_id:
            followers_to_add.append(self.env.user.partner_id.id)
        # Add sale order salesperson if available
        if self.project_id.sale_order_id and self.project_id.sale_order_id.user_id:
            followers_to_add.append(self.project_id.sale_order_id.user_id.partner_id.id)
        
        if followers_to_add:
            self.message_subscribe(partner_ids=list(set(followers_to_add)))
        
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
            'status': 'confirmed',
            'vendor_signature': signature,
            'vendor_signature_date': fields.Datetime.now(),
        })
        
        # Get service type display name
        service_type_label = dict(self._fields['service_type'].selection).get(
            self.service_type, self.service_type
        )
        
        # Notify project manager
        self.project_id.message_post(
            body=_("%s accepted %s assignment for %s") % (
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
        
        self.write({
            'status': 'declined',
            'vendor_decline_reason': reason or _("No reason provided"),
        })
        
        # Get service type display name
        service_type_label = dict(self._fields['service_type'].selection).get(
            self.service_type, self.service_type
        )
        
        # URGENT notification to project manager
        self.project_id.message_post(
            body=_("URGENT: %s declined %s assignment!<br/>Reason: %s") % (
                self.vendor_id.name,
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
    
    def action_preview_vendor_portal(self):
        """Open the vendor portal page in a new browser tab.
        
        This allows internal team members to see exactly what the vendor
        sees when they access their work order via the portal.
        
        Returns:
            dict: URL action to open portal page in new tab.
        """
        self.ensure_one()
        
        # Generate access token if not exists
        token = self._get_access_token()
        
        # Build the portal URL
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        portal_url = f"{base_url}/my/work-orders/{self.id}/{token}"
        
        return {
            'type': 'ir.actions.act_url',
            'url': portal_url,
            'target': 'new',
        }
    
    def action_mark_completed(self):
        """Mark work order as completed (after event)."""
        self.ensure_one()
        self.status = 'completed'
        return True

    @api.model
    def _cron_remind_pending_work_orders(self):
        """Send reminders for pending work orders older than 24 hours."""
        now = fields.Datetime.now()
        cutoff = now - timedelta(hours=24)
        domain = [
            ("status", "=", "pending"),
            ("create_date", "<=", cutoff),
            "|", ("last_reminder_date", "=", False), ("last_reminder_date", "<=", cutoff),
        ]
        pending = self.search(domain)
        template = self.env.ref(
            "ptt_vendor_management.email_template_vendor_work_order_reminder",
            raise_if_not_found=False,
        )
        for assignment in pending:
            if template and assignment.vendor_id and assignment.vendor_id.email:
                template.send_mail(assignment.id, force_send=True)
                assignment.last_reminder_date = now

    def action_view_tasks(self):
        """Open the list of vendor tasks for this assignment."""
        self.ensure_one()
        return {
            'name': _('Vendor Tasks'),
            'type': 'ir.actions.act_window',
            'res_model': 'ptt.vendor.task',
            'view_mode': 'list,kanban,form',
            'domain': [('assignment_id', '=', self.id)],
            'context': {
                'default_assignment_id': self.id,
            },
        }

