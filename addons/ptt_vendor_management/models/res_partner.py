# Part of Party Time Texas Event Management System
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
"""
Partner extensions for vendor portal access.
"""

from odoo import models, fields, api


class ResPartnerVendorPortal(models.Model):
    """Portal extensions for vendor partners."""
    _inherit = "res.partner"
    
    # Portal vendor access
    ptt_vendor_portal_access = fields.Boolean(
        string="Vendor Portal Access",
        default=False,
        help="Allow this vendor to access the vendor portal"
    )
    
    # All assignments (no domain on One2many - use computed for filtered access)
    ptt_all_assignment_ids = fields.One2many(
        "ptt.project.vendor.assignment",
        "vendor_id",
        string="All Assignments",
    )
    
    # Computed field for active (non-cancelled) assignments
    ptt_portal_assignment_ids = fields.Many2many(
        "ptt.project.vendor.assignment",
        string="Portal Assignments",
        compute="_compute_portal_assignments",
        help="Active assignments visible in vendor portal (excludes cancelled)"
    )
    ptt_active_assignment_count = fields.Integer(
        string="Active Assignments",
        compute="_compute_portal_assignments",
    )
    
    @api.depends("ptt_all_assignment_ids", "ptt_all_assignment_ids.status")
    def _compute_portal_assignments(self):
        """Compute active assignments for vendor portal view.
        
        Filters out cancelled assignments and counts those in
        active states (pending, confirmed, in_progress).
        """
        for partner in self:
            # Filter out cancelled assignments for portal view
            active_assignments = partner.ptt_all_assignment_ids.filtered(
                lambda a: a.status not in ('cancelled',)
            )
            partner.ptt_portal_assignment_ids = active_assignments
            partner.ptt_active_assignment_count = len(
                active_assignments.filtered(
                    lambda a: a.status in ('pending', 'confirmed', 'in_progress')
                )
            )
    
    def action_view_vendor_assignments(self):
        """View all vendor assignments for this partner."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Vendor Assignments',
            'res_model': 'ptt.project.vendor.assignment',
            'view_mode': 'list,form',
            'domain': [('vendor_id', '=', self.id)],
            'context': {'default_vendor_id': self.id},
        }
