# Part of Party Time Texas Event Management System
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
"""
Project extensions for PTT Enhanced Sales.

NOTE: ptt_event_type field is now defined in ptt_business_core/models/project_project.py
to ensure correct module load order (ptt_business_core views use this field).
"""

from odoo import models


class ProjectProject(models.Model):
    """Extend project for PTT Enhanced Sales integration."""
    _inherit = 'project.project'

    # ==========================================================================
    # NOTE: ptt_event_type field is now defined in ptt_business_core
    # ==========================================================================
    # This ensures the field exists when ptt_business_core views load.
    pass
