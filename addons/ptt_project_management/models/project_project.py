# Part of Party Time Texas Event Management System
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import models, fields, api, _

from odoo.addons.ptt_business_core.constants import EVENT_STATUS


class ProjectProject(models.Model):
    """Enhanced Project for Event Management"""
    _inherit = 'project.project'

    # Template Integration
    template_id = fields.Many2one(
        'project.template',
        string="Project Template",
        help="Template used to create this project"
    )
    
    # Stakeholder Management
    stakeholder_ids = fields.One2many(
        'project.stakeholder',
        'project_id',
        string="Stakeholders",
        help="All stakeholders involved in this event project"
    )
    
    # Stakeholder Counts for Dashboard
    vendor_count = fields.Integer(
        string="Number of Vendors",
        compute='_compute_stakeholder_counts',
        store=True
    )
    
    client_count = fields.Integer(
        string="Number of Clients",
        compute='_compute_stakeholder_counts',
        store=True
    )
    
    internal_count = fields.Integer(
        string="Internal Team Size",
        compute='_compute_stakeholder_counts',
        store=True
    )
    
    confirmed_stakeholders = fields.Integer(
        string="Confirmed Stakeholders",
        compute='_compute_stakeholder_status',
        store=True
    )
    
    pending_stakeholders = fields.Integer(
        string="Pending Stakeholders",
        compute='_compute_stakeholder_status',
        store=True
    )
    
    # Event Status
    event_status = fields.Selection(
        selection=EVENT_STATUS,
        string="Event Status",
        default='planning'
    )
    
    # NOTE: Event type is defined as ptt_event_type_id in ptt_enhanced_sales
    # Do not add a duplicate field here
    
    @api.depends('stakeholder_ids.is_vendor', 'stakeholder_ids.is_client', 'stakeholder_ids.is_internal')
    def _compute_stakeholder_counts(self):
        """Compute stakeholder counts by type (vendor/client/internal).
        
        These counts are displayed on the project dashboard for
        quick visibility into event staffing.
        """
        for project in self:
            project.vendor_count = len(project.stakeholder_ids.filtered('is_vendor'))
            project.client_count = len(project.stakeholder_ids.filtered('is_client'))
            project.internal_count = len(project.stakeholder_ids.filtered('is_internal'))
    
    @api.depends('stakeholder_ids.status')
    def _compute_stakeholder_status(self):
        """Compute stakeholder confirmation status counts.
        
        Tracks how many stakeholders are confirmed vs pending
        to help event coordinators track readiness.
        """
        for project in self:
            project.confirmed_stakeholders = len(project.stakeholder_ids.filtered(lambda s: s.status == 'confirmed'))
            project.pending_stakeholders = len(project.stakeholder_ids.filtered(lambda s: s.status == 'pending'))
    
    def action_view_stakeholders(self):
        """Open list view of all stakeholders for this project.
        
        Returns:
            dict: Action to open stakeholder list filtered by project.
        """
        return {
            'type': 'ir.actions.act_window',
            'name': 'Event Stakeholders',
            'res_model': 'project.stakeholder',
            'view_mode': 'tree,form',
            'domain': [('project_id', '=', self.id)],
            'context': {'default_project_id': self.id},
            'target': 'current',
        }
    
    def action_view_vendors(self):
        """Open list view of vendor stakeholders only.
        
        Returns:
            dict: Action to open vendor stakeholder list.
        """
        return {
            'type': 'ir.actions.act_window',
            'name': 'Event Vendors',
            'res_model': 'project.stakeholder',
            'view_mode': 'tree,form',
            'domain': [('project_id', '=', self.id), ('is_vendor', '=', True)],
            'context': {'default_project_id': self.id, 'default_is_vendor': True},
            'target': 'current',
        }
    
    def action_view_clients(self):
        """Open list view of client stakeholders only.
        
        Returns:
            dict: Action to open client stakeholder list.
        """
        return {
            'type': 'ir.actions.act_window',
            'name': 'Event Clients',
            'res_model': 'project.stakeholder',
            'view_mode': 'tree,form',
            'domain': [('project_id', '=', self.id), ('is_client', '=', True)],
            'context': {'default_project_id': self.id, 'default_is_client': True},
            'target': 'current',
        }
    
    def action_confirm_all_stakeholders(self):
        """Bulk confirm all pending stakeholders.
        
        Iterates through pending stakeholders and confirms each one,
        triggering individual confirmation notifications.
        
        Returns:
            dict: Notification action with count of confirmed stakeholders.
        """
        pending_stakeholders = self.stakeholder_ids.filtered(lambda s: s.status == 'pending')
        for stakeholder in pending_stakeholders:
            stakeholder.action_confirm_stakeholder()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': f'Confirmed {len(pending_stakeholders)} stakeholders',
                'type': 'success',
            }
        }
    
    def action_send_stakeholder_notifications(self):
        """Send notifications to all confirmed stakeholders.
        
        Emails are sent only to stakeholders with confirmed status
        and valid email addresses.
        
        Returns:
            dict: Notification action with count of emails sent.
        """
        confirmed_stakeholders = self.stakeholder_ids.filtered(lambda s: s.status == 'confirmed')
        
        notification_count = 0
        for stakeholder in confirmed_stakeholders:
            if stakeholder.partner_id.email:
                stakeholder._send_confirmation_notification()
                notification_count += 1
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': f'Sent notifications to {notification_count} stakeholders',
                'type': 'success',
            }
        }
    
    @api.model
    def create_from_template(self, template_id, project_vals=None):
        """Create a new project from a template.
        
        Args:
            template_id: ID of the project.template to use.
            project_vals: Optional dict of additional project values.
            
        Returns:
            project.project: The newly created project record.
        """
        template = self.env['project.template'].browse(template_id)
        return template.create_project_from_template(project_vals)
    
    def action_apply_template(self):
        """Apply a template to existing project.
        
        Note: This opens a selection view to pick a template.
        The actual template application is handled by project.template.apply_to_project()
        """
        return {
            'type': 'ir.actions.act_window',
            'name': 'Select Template',
            'res_model': 'project.template',
            'view_mode': 'tree,form',
            'context': {'apply_to_project_id': self.id},
            'target': 'current',
        }