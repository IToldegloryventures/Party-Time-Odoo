# Part of Party Time Texas Event Management System
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import models, fields, api


class ProjectProject(models.Model):
    """Extend project with event type link from sale.order.type."""
    _inherit = 'project.project'

    ptt_event_type_id = fields.Many2one(
        'sale.order.type',
        string="Event Template",
        help="Event type template from sale.order.type (Corporate, Wedding, Social, etc.)"
    )

    @api.onchange('ptt_event_type_id')
    def _onchange_ptt_event_type_id(self):
        """Sync ptt_event_type selection field when template is changed."""
        if self.ptt_event_type_id:
            type_name = self.ptt_event_type_id.name.lower() if self.ptt_event_type_id.name else ''
            if 'corporate' in type_name:
                self.ptt_event_type = 'corporate'
            elif 'wedding' in type_name:
                self.ptt_event_type = 'wedding'
            elif 'social' in type_name:
                self.ptt_event_type = 'social'

    @api.onchange('ptt_event_type')
    def _onchange_ptt_event_type(self):
        """Sync ptt_event_type_id template when selection field is changed."""
        if self.ptt_event_type and not self.ptt_event_type_id:
            xmlid_map = {
                'corporate': 'ptt_enhanced_sales.event_type_corporate',
                'social': 'ptt_enhanced_sales.event_type_social',
                'wedding': 'ptt_enhanced_sales.event_type_wedding',
            }
            xmlid = xmlid_map.get(self.ptt_event_type)
            if xmlid:
                event_type = self.env.ref(xmlid, raise_if_not_found=False)
                if event_type:
                    self.ptt_event_type_id = event_type
