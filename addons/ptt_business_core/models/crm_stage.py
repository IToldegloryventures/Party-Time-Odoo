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
    - data/rename_default_crm_stages.xml (renames default Odoo stages)
    - data/crm_stages.xml (creates additional stages)
    - pre_init_hook in __init__.py (cleans up orphaned stages)
    """
    _inherit = 'crm.stage'
    # No custom fields or methods needed - just documentation
