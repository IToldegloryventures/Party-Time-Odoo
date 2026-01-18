# Part of Party Time Texas Event Management System
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from markupsafe import Markup, escape as html_escape
from odoo import models, fields, api, _
from odoo.exceptions import UserError

from odoo.addons.ptt_business_core.constants import (
    SERVICE_TYPES,
    COMMUNICATION_PREFERENCES,
    STAKEHOLDER_STATUS,
)


class ProjectStakeholder(models.Model):
    """Project Stakeholders for Event Management"""
    _name = 'project.stakeholder'
    _description = 'Project Stakeholder'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'project_id, sequence, role'

    project_id = fields.Many2one(
        'project.project',
        string="Project",
        required=True,
        ondelete='cascade',
        index=True,
    )
    
    sequence = fields.Integer(
        string="Sequence",
        default=10
    )
    
    partner_id = fields.Many2one(
        'res.partner',
        string="Contact",
        required=True,
        help="The partner/contact for this stakeholder"
    )
    
    role = fields.Char(
        string="Role",
        required=True,
        help="Role of this stakeholder (e.g., Event Coordinator, DJ, Photographer)"
    )
    
    responsibility = fields.Text(
        string="Responsibility",
        help="Description of this stakeholder's responsibilities"
    )
    
    # Stakeholder Type
    is_vendor = fields.Boolean(
        string="Is Vendor",
        default=False
    )
    
    is_client = fields.Boolean(
        string="Is Client", 
        default=False
    )
    
    is_internal = fields.Boolean(
        string="Is Internal Team",
        default=False
    )
    
    # Contact Information (from partner)
    email = fields.Char(
        related='partner_id.email',
        string="Email",
        readonly=True
    )
    
    phone = fields.Char(
        related='partner_id.phone',
        string="Phone",
        readonly=True
    )
    
    mobile = fields.Char(
        related='partner_id.phone',
        string="Mobile",
        readonly=True
    )
    
    # Communication Preferences
    communication_preference = fields.Selection(
        selection=COMMUNICATION_PREFERENCES,
        string="Preferred Communication",
        default='email'
    )
    
    # Service Category for Vendors - uses SERVICE_TYPES from constants.py
    vendor_category = fields.Selection(
        selection=SERVICE_TYPES,
        string="Service Category"
    )
    
    # Status and Availability
    status = fields.Selection(
        selection=STAKEHOLDER_STATUS,
        string="Status",
        default='pending',
        tracking=True
    )
    
    confirmed_date = fields.Datetime(
        string="Confirmation Date",
        help="When this stakeholder confirmed their participation"
    )
    
    # Requirements and Notes
    required_for_event = fields.Boolean(
        string="Required for Event",
        default=True,
        help="This stakeholder is required for the event to proceed"
    )
    
    special_requirements = fields.Text(
        string="Special Requirements",
        help="Any special requirements or notes for this stakeholder"
    )
    
    # Event-specific details
    arrival_time = fields.Datetime(
        string="Expected Arrival Time",
        help="When this stakeholder should arrive at the venue"
    )
    
    departure_time = fields.Datetime(
        string="Expected Departure Time",
        help="When this stakeholder is expected to leave"
    )
    
    # Portal Access
    has_portal_access = fields.Boolean(
        string="Has Portal Access",
        compute='_compute_has_portal_access',
        readonly=True
    )
    
    @api.depends('partner_id', 'partner_id.user_ids')
    def _compute_has_portal_access(self):
        """Check if stakeholder's partner has portal user access."""
        for stakeholder in self:
            stakeholder.has_portal_access = bool(stakeholder.partner_id.user_ids)
    
    # Related vendor assignment from ptt_business_core
    vendor_assignment_id = fields.Many2one(
        'ptt.project.vendor.assignment',
        string="Vendor Assignment",
        help="Related vendor assignment for cost tracking"
    )
    
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """Auto-populate fields based on partner.
        
        Sets vendor flag if partner is marked as vendor and
        determines default communication preference.
        """
        if self.partner_id:
            # Check if partner is marked as vendor in ptt_business_core
            if hasattr(self.partner_id, 'ptt_is_vendor') and self.partner_id.ptt_is_vendor:
                self.is_vendor = True
                self.is_internal = False
            
            # Set default communication preference based on partner settings
            if self.partner_id.email:
                self.communication_preference = 'email'
            elif self.partner_id.phone:
                self.communication_preference = 'phone'
    
    @api.onchange('is_vendor', 'vendor_category')
    def _onchange_vendor_details(self):
        """Auto-set role based on vendor category.
        
        Maps vendor service categories to appropriate role names.
        """
        if self.is_vendor and self.vendor_category:
            category_roles = {
                'dj': 'DJ/MC',
                'photovideo': 'Photographer/Videographer',
                'lighting': 'Lighting/AV Technician',
                'decor': 'Decorator',
                'catering': 'Catering Coordinator',
                'venue_sourcing': 'Venue Coordinator',
                'staffing': 'Event Staff',
                'transportation': 'Transportation Coordinator',
                'coordination': 'Event Coordinator',
                'other': 'Vendor',
            }
            if not self.role:
                self.role = category_roles.get(self.vendor_category, 'Vendor')
    
    def action_confirm_stakeholder(self):
        """Confirm stakeholder participation in the event.
        
        Sets status to confirmed, records confirmation timestamp,
        and sends notification email to the stakeholder.
        """
        self.status = 'confirmed'
        self.confirmed_date = fields.Datetime.now()
        
        # Send confirmation notification
        self._send_confirmation_notification()
    
    def action_mark_unavailable(self):
        """Mark stakeholder as unavailable"""
        self.status = 'unavailable'
        
        # Log message about unavailability (escaped for safety)
        self.project_id.message_post(
            body=Markup(_("Stakeholder <b>{}</b> ({}) marked as unavailable")).format(
                html_escape(self.partner_id.name or ''),
                html_escape(self.role or '')
            ),
            message_type='notification'
        )
    
    def action_cancel(self):
        """Cancel stakeholder participation"""
        self.status = 'cancelled'
        
        # Log cancellation (escaped for safety)
        self.project_id.message_post(
            body=Markup(_("Stakeholder <b>{}</b> ({}) cancelled")).format(
                html_escape(self.partner_id.name or ''),
                html_escape(self.role or '')
            ),
            message_type='notification'
        )
    
    def _send_confirmation_notification(self):
        """Send notification when stakeholder is confirmed"""
        if self.partner_id.email and self.communication_preference == 'email':
            # Get event details from project (ptt_ prefixed fields from ptt_business_core)
            event_date = getattr(self.project_id, 'ptt_event_date', None) or 'TBD'
            venue_name = getattr(self.project_id, 'ptt_venue_name', None) or 'TBD'
            
            # Properly escape user-provided content to prevent XSS
            partner_name = html_escape(self.partner_id.name or '')
            role_escaped = html_escape(self.role or '')
            project_name = html_escape(self.project_id.name or '')
            event_date_escaped = html_escape(str(event_date))
            venue_escaped = html_escape(str(venue_name))
            
            # Create mail message with escaped content
            body_html = Markup('''
                <p>Dear {partner_name},</p>
                <p>You have been confirmed as <strong>{role}</strong> for the event:</p>
                <p><strong>Event:</strong> {project_name}</p>
                <p><strong>Date:</strong> {event_date}</p>
                <p><strong>Venue:</strong> {venue_name}</p>
                <p>We will contact you with additional details as the event approaches.</p>
                <p>Thank you for your participation!</p>
                <p>- Party Time Texas Team</p>
            ''').format(
                partner_name=partner_name,
                role=role_escaped,
                project_name=project_name,
                event_date=event_date_escaped,
                venue_name=venue_escaped,
            )
            
            # Use Odoo's configured email settings
            # Priority: User email → Company email → Catchall alias
            company = self.env.company
            email_from = (
                self.env.user.email
                or company.email
                or company.catchall_formatted
            )
            
            if not email_from:
                raise UserError(_('No email configured. Please set an email in your user profile or company settings.'))
            
            mail_values = {
                'subject': _('Event Confirmation - %s') % self.project_id.name,
                'body_html': body_html,
                'email_to': self.partner_id.email,
                'email_from': email_from,
            }
            
            mail = self.env['mail.mail'].create(mail_values)
            mail.send()
    
    def action_open_partner(self):
        """Open the partner form"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Contact Details',
            'res_model': 'res.partner',
            'res_id': self.partner_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def action_create_vendor_assignment(self):
        """Create vendor assignment for cost tracking"""
        if not self.is_vendor:
            return
        
        # Check if vendor assignment already exists
        if self.vendor_assignment_id:
            return self.vendor_assignment_id.action_open_form()
        
        # Create new vendor assignment
        assignment_vals = {
            'project_id': self.project_id.id,
            'vendor_id': self.partner_id.id,
            'service_type': self.vendor_category,
            'description': f"{self.role} - {self.responsibility or ''}",
        }
        
        assignment = self.env['ptt.project.vendor.assignment'].create(assignment_vals)
        self.vendor_assignment_id = assignment.id
        
        return assignment.action_open_form()
