# Part of Party Time Texas Event Management System
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
"""
Enhanced Project model for Party Time Texas event management.

NOTE: Project templates are now native Odoo project.project records with is_template=True.
Only the Social template remains (see ptt_business_core/data/project_template.xml).

When a Sale Order with Event Kickoff product is confirmed, Odoo's native template
copying mechanism creates the project with all tasks and subtasks from the template.
"""

from odoo import models, fields, api, _

from odoo.addons.ptt_business_core.constants import EVENT_STATUS


class ProjectProject(models.Model):
    """Enhanced Project for Event Management"""
    _inherit = 'project.project'

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
            'view_mode': 'list,form',
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
            'view_mode': 'list,form',
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
