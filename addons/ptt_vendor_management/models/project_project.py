# Part of Party Time Texas Event Management System
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

"""
Extend project.project with RFQ integration for vendor management.

Adds RFQ count field and smart button to easily view/manage RFQs for an event.
"""
from odoo import models, fields, api, _


class ProjectProject(models.Model):
    """Extend project with RFQ count and navigation."""
    _inherit = 'project.project'

    # === VENDOR WORK ORDERS ===
    vendor_work_order_count = fields.Integer(
        string="Work Orders",
        compute='_compute_vendor_work_orders',
        store=True,
        help="Number of vendor work orders for this project",
    )

    vendor_pending_response_count = fields.Integer(
        string="Pending Vendor Responses",
        compute='_compute_vendor_work_orders',
        store=True,
        help="Number of vendor work orders awaiting response",
    )

    # === RFQ INTEGRATION ===
    rfq_ids = fields.One2many(
        'ptt.vendor.rfq',
        'project_id',
        string="RFQs",
        help="Vendor RFQs (Requests for Quote) for this event project",
    )
    
    rfq_count = fields.Integer(
        string="RFQ Count",
        compute='_compute_rfq_count',
        store=True,
        help="Number of vendor RFQs for this project",
    )
    
    rfq_pending_count = fields.Integer(
        string="Pending RFQs",
        compute='_compute_rfq_count',
        store=True,
        help="Number of RFQs awaiting vendor responses",
    )
    
    @api.depends('rfq_ids', 'rfq_ids.state')
    def _compute_rfq_count(self):
        """Compute RFQ counts for smart button display."""
        for project in self:
            project.rfq_count = len(project.rfq_ids)
            project.rfq_pending_count = len(project.rfq_ids.filtered(
                lambda r: r.state == 'in_progress'
            ))

    @api.depends('ptt_vendor_assignment_ids', 'ptt_vendor_assignment_ids.status')
    def _compute_vendor_work_orders(self):
        """Compute work order counts for smart buttons."""
        for project in self:
            assignments = project.ptt_vendor_assignment_ids
            project.vendor_work_order_count = len(assignments)
            project.vendor_pending_response_count = len(
                assignments.filtered(lambda a: a.status == 'pending')
            )
    
    def action_view_rfqs(self):
        """Open RFQs for this project.
        
        Opens Kanban view by default for visual management.
        
        Returns:
            dict: Action to open RFQ list filtered by project.
        """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Vendor RFQs'),
            'res_model': 'ptt.vendor.rfq',
            'view_mode': 'kanban,list,form',
            'domain': [('project_id', '=', self.id)],
            'context': {
                'default_project_id': self.id,
                'search_default_filter_in_progress': 1,
            },
            'target': 'current',
        }

    def action_view_vendor_work_orders(self):
        """Open all vendor work orders for this project."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Vendor Work Orders'),
            'res_model': 'ptt.project.vendor.assignment',
            'view_mode': 'list,form',
            'domain': [('project_id', '=', self.id)],
            'context': {
                'default_project_id': self.id,
            },
            'target': 'current',
        }

    def action_view_pending_vendor_responses(self):
        """Open vendor work orders awaiting response."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Pending Vendor Responses'),
            'res_model': 'ptt.project.vendor.assignment',
            'view_mode': 'list,form',
            'domain': [
                ('project_id', '=', self.id),
                ('status', '=', 'pending'),
            ],
            'context': {
                'default_project_id': self.id,
                'search_default_filter_pending': 1,
            },
            'target': 'current',
        }
