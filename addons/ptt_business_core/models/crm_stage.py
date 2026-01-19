# -*- coding: utf-8 -*-
# Part of Party Time Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class CrmStage(models.Model):
    """Extend CRM Stage model.
    
    PTT CRM Stages (in order):
    1. Intake (renamed from New)
    2. Qualification (renamed from Qualified)
    3. Approval
    4. Proposal Sent (renamed from Proposition)
    5. Contract Sent
    6. Booked
    7. Closed/Won (renamed from Won)
    8. Lost
    
    Stage management is handled via:
    - data/crm_stages.xml (creates/renames stages)
    
    Note: No custom fields or methods needed - just documentation.
    The stage automation is handled in sale_order.py overrides.
    """
    _inherit = 'crm.stage'
    # No custom fields or methods needed - just documentation
