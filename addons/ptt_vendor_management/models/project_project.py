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
