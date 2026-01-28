# Part of Party Time Texas Event Management System
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import models


class ProjectProject(models.Model):
    """Extend project with event type link from sale.order.type."""
    _inherit = 'project.project'

    # Field is defined in ptt_business_core as a related; no extra logic needed here.
