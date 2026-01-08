from odoo import models, api
import logging

_logger = logging.getLogger(__name__)


class CrmStage(models.Model):
    """Extend CRM Stage to cleanup unwanted stages on module update."""
    _inherit = 'crm.stage'

    @api.model_create_multi
    def create(self, vals_list):
        """Prevent creation of unwanted stages."""
        # List of stages that should not exist (use alternatives instead)
        unwanted_stages = ['Qualified', 'Quote Sent', 'Approval', 'Execution', 'New']
        
        for vals in vals_list:
            if vals.get('name') in unwanted_stages:
                _logger.warning(
                    f"Skipping creation of unwanted stage: {vals.get('name')}. "
                    f"Use alternatives: Qualified→Qualification, Quote Sent→Proposal Sent"
                )
                # Don't create it
                continue
        
        return super().create(vals_list)
