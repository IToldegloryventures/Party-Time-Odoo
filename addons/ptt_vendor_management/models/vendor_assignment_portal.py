# Part of Party Time Texas Event Management System
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
"""
Vendor Assignment Portal Extensions.

Extends the base ptt.project.vendor.assignment model with portal-specific
functionality for vendors to view and manage their assignments.
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.exceptions import AccessError


class PttVendorAssignmentPortal(models.Model):
    """Portal extensions for vendor assignments."""
    _inherit = "ptt.project.vendor.assignment"
    
    # Token expiration default: 30 days
    _TOKEN_EXPIRY_DAYS = 30
    
    # Portal access token for secure access
    access_token = fields.Char(
        string="Access Token",
        copy=False,
        help="Unique token for portal access"
    )
    access_token_expires = fields.Datetime(
        string="Token Expires",
        copy=False,
        help="When the access token expires"
    )
    
    # Vendor confirmation workflow
    vendor_confirmed = fields.Boolean(
        string="Vendor Confirmed",
        default=False,
        tracking=True,
        help="Has the vendor confirmed this assignment"
    )
    vendor_confirmed_date = fields.Datetime(
        string="Confirmation Date",
        readonly=True,
    )
    vendor_confirmed_by = fields.Many2one(
        "res.users",
        string="Confirmed By",
        readonly=True,
    )
    
    # Vendor notes (visible to vendor on portal)
    vendor_notes = fields.Text(
        string="Vendor Notes",
        help="Notes from the vendor about this assignment"
    )
    
    # Documents for vendor
    document_ids = fields.One2many(
        "ptt.vendor.document",
        "vendor_assignment_id",
        string="Documents",
    )
    document_count = fields.Integer(
        string="Document Count",
        compute="_compute_document_count",
    )
    
    @api.depends("document_ids")
    def _compute_document_count(self):
        """Compute count of documents attached to this assignment."""
        for record in self:
            record.document_count = len(record.document_ids)
    
    def _generate_access_token(self, expiry_days=None):
        """Generate a unique access token for portal access with expiration.
        
        Args:
            expiry_days: Number of days until token expires. Defaults to _TOKEN_EXPIRY_DAYS (30).
        
        Returns:
            str: The generated access token.
        """
        import secrets
        from datetime import timedelta
        
        self.ensure_one()
        if expiry_days is None:
            expiry_days = self._TOKEN_EXPIRY_DAYS
        
        self.access_token = secrets.token_urlsafe(32)
        self.access_token_expires = fields.Datetime.now() + timedelta(days=expiry_days)
        return self.access_token
    
    def _is_token_valid(self, token):
        """Check if the provided access token is valid and not expired.
        
        Args:
            token: The access token to validate.
            
        Returns:
            bool: True if token is valid and not expired.
        """
        self.ensure_one()
        if not self.access_token or not token:
            return False
        if self.access_token != token:
            return False
        if self.access_token_expires and self.access_token_expires < fields.Datetime.now():
            return False
        return True

    def action_vendor_confirm(self):
        """Vendor confirms acceptance of the assignment.
        
        Records confirmation timestamp, user, and updates status.
        Posts a notification to the chatter for audit trail.
        
        Returns:
            bool: True on success.
        """
        self.ensure_one()
        self.write({
            'vendor_confirmed': True,
            'vendor_confirmed_date': fields.Datetime.now(),
            'vendor_confirmed_by': self.env.user.id,
            'status': 'confirmed',
        })
        # Post a message
        self.message_post(
            body=_("Assignment confirmed by vendor %s") % self.env.user.name,
            message_type='notification',
        )
        return True
    
    def action_vendor_decline(self):
        """Vendor declines the assignment.
        
        Sets status to cancelled and posts notification.
        
        Returns:
            bool: True on success.
        """
        self.ensure_one()
        self.write({
            'vendor_confirmed': False,
            'status': 'cancelled',
        })
        self.message_post(
            body=_("Assignment declined by vendor %s") % self.env.user.name,
            message_type='notification',
        )
        return True
    
    def action_send_vendor_invite(self):
        """Send portal invite to vendor.
        
        Generates access token, creates portal user if needed,
        and sends invitation email with assignment details.
        
        Raises:
            UserError: If vendor or email is not configured.
        """
        self.ensure_one()
        if not self.vendor_id:
            raise UserError(_('No vendor assigned to this assignment.'))
        
        if not self.vendor_id.email:
            raise UserError(_('Vendor %s has no email address configured.') % self.vendor_id.name)
        
        # Generate access token for this assignment
        self._generate_access_token()
        
        # Check if user already exists for this partner
        user = self.env['res.users'].sudo().search([
            ('partner_id', '=', self.vendor_id.id)
        ], limit=1)
        
        if user:
            # User exists - ensure portal access and send password reset
            portal_group = self.env.ref('base.group_portal', raise_if_not_found=False)
            if portal_group and portal_group not in user.groups_id:
                user.groups_id = [(4, portal_group.id)]
            user.partner_id.signup_prepare()
            user.action_reset_password()
        else:
            # Create new portal user using standard method
            portal_group = self.env.ref('base.group_portal')
            user = self.env['res.users'].with_context(
                no_reset_password=False
            ).sudo()._create_user_from_template({
                'email': self.vendor_id.email,
                'login': self.vendor_id.email,
                'partner_id': self.vendor_id.id,
                'company_id': self.env.company.id,
                'company_ids': [(6, 0, self.env.company.ids)],
                'groups_id': [(6, 0, [portal_group.id])],
                'active': True,
            })
            # Prepare signup token and send invite
            user.partner_id.signup_prepare()
            user.action_reset_password()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Portal Invite Sent'),
                'message': _('Portal access email sent to %s') % self.vendor_id.email,
                'type': 'success',
                'sticky': False,
            },
        }
    
    def _get_portal_url(self):
        """Get the portal URL for this assignment."""
        self.ensure_one()
        return f"/my/vendor/assignment/{self.id}?access_token={self.access_token}"


class PttVendorDocument(models.Model):
    """Documents shared with vendors for assignments."""
    _name = "ptt.vendor.document"
    _description = "Vendor Assignment Document"
    _order = "create_date desc"
    
    name = fields.Char(
        string="Document Name",
        required=True,
    )
    vendor_assignment_id = fields.Many2one(
        "ptt.project.vendor.assignment",
        string="Vendor Assignment",
        required=True,
        ondelete="cascade",
    )
    document_type = fields.Selection([
        ('contract', 'Contract'),
        ('instructions', 'Event Instructions'),
        ('timeline', 'Timeline/Schedule'),
        ('floor_plan', 'Floor Plan'),
        ('song_list', 'Song List'),
        ('photos', 'Reference Photos'),
        ('other', 'Other'),
    ], string="Document Type", default='other')
    
    attachment_id = fields.Many2one(
        "ir.attachment",
        string="Attachment",
    )
    file = fields.Binary(
        string="File",
        attachment=True,
    )
    filename = fields.Char(string="Filename")
    
    notes = fields.Text(string="Notes")
    
    # Visibility
    visible_to_vendor = fields.Boolean(
        string="Visible to Vendor",
        default=True,
    )
