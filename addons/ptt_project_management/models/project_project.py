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
    
    # Stakeholder Management (Simple Contact Directory)
    stakeholder_ids = fields.One2many(
        'project.stakeholder',
        'project_id',
        string="Stakeholders",
        help="Contact directory for this event - clients, vendors, key contacts"
    )
    
    # Simple Stakeholder Counts for smart buttons
    vendor_count = fields.Integer(
        string="Vendors",
        compute='_compute_stakeholder_counts',
        store=True
    )
    
    client_count = fields.Integer(
        string="Clients",
        compute='_compute_stakeholder_counts',
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
    
    @api.depends('stakeholder_ids.is_vendor', 'stakeholder_ids.is_client')
    def _compute_stakeholder_counts(self):
        """Compute stakeholder counts by type."""
        for project in self:
            project.vendor_count = len(project.stakeholder_ids.filtered('is_vendor'))
            project.client_count = len(project.stakeholder_ids.filtered('is_client'))
    
    def action_view_stakeholders(self):
        """Open list view of all stakeholders for this project."""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Event Contacts',
            'res_model': 'project.stakeholder',
            'view_mode': 'tree,form',
            'domain': [('project_id', '=', self.id)],
            'context': {'default_project_id': self.id},
            'target': 'current',
        }
    
    def action_view_crm_lead(self):
        """Open the source CRM opportunity for this project.
        
        Returns:
            dict: Action to open the CRM lead form.
        """
        self.ensure_one()
        if not self.ptt_crm_lead_id:
            return {'type': 'ir.actions.act_window_close'}
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Source Opportunity'),
            'res_model': 'crm.lead',
            'view_mode': 'form',
            'res_id': self.ptt_crm_lead_id.id,
            'target': 'current',
        }
    
    def action_view_sale_order(self):
        """Open the source sale order for this project.
        
        Returns:
            dict: Action to open the sale order form.
        """
        self.ensure_one()
        if not self.sale_order_id:
            return {'type': 'ir.actions.act_window_close'}
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Sale Order'),
            'res_model': 'sale.order',
            'view_mode': 'form',
            'res_id': self.sale_order_id.id,
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
        """Open list view of client stakeholders only."""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Event Clients',
            'res_model': 'project.stakeholder',
            'view_mode': 'list,form',
            'domain': [('project_id', '=', self.id), ('is_client', '=', True)],
            'context': {'default_project_id': self.id, 'default_is_client': True},
            'target': 'current',
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
