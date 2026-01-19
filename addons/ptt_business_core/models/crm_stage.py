# -*- coding: utf-8 -*-
# Part of Party Time Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class CrmStage(models.Model):
    """Extend CRM Stage model.
    
    PTT CRM Pipeline Stages (configured in data/crm_stages.xml):
    
    Seq  | Stage Name      | XML ID                        | Won?  | Notes
    -----|-----------------|-------------------------------|-------|---------------------------
    10   | Intake          | crm.stage_lead1               | No    | New inquiry received
    20   | Qualification   | crm.stage_lead2               | No    | Lead qualified
    30   | Approval        | crm.stage_lead3               | No    | Internal approval needed
    40   | Proposal Sent   | stage_ptt_proposal_sent       | No    | Quote sent to customer
    50   | Contract Sent   | stage_ptt_contract_sent       | No    | Contract awaiting signature
    60   | Booked          | crm.stage_lead4               | Yes   | Event confirmed (Won)
    100  | Lost            | stage_ptt_lost                | No    | Opportunity lost (folded)
    
    Stage Automation (handled in crm_lead.py and sale_order.py):
    - Intake → Qualification: Manual or when lead is qualified
    - Qualification → Approval: When proposal needs internal approval
    - Approval → Proposal Sent: Auto when quotation is sent
    - Proposal Sent → Contract Sent: When contract is generated
    - Contract Sent → Booked: Auto when sale order is confirmed
    - Any → Lost: Manual when opportunity is lost
    """
    _inherit = 'crm.stage'
    # No custom fields needed - stage configuration is in data/crm_stages.xml
