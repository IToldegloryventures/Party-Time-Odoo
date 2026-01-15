# -*- coding: utf-8 -*-

from odoo import api, fields, models


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    justcall_call_ids = fields.One2many(
        'ptt.justcall.call',
        'lead_id',
        string="JustCall Calls",
    )
    justcall_call_count = fields.Integer(
        string="Call Count",
        compute='_compute_justcall_call_count',
    )
    justcall_last_call_date = fields.Datetime(
        string="Last Call Date",
        compute='_compute_justcall_call_info',
    )

    @api.depends('justcall_call_ids')
    def _compute_justcall_call_count(self):
        """Compute call count"""
        for lead in self:
            lead.justcall_call_count = len(lead.justcall_call_ids)

    @api.depends('justcall_call_ids.call_date')
    def _compute_justcall_call_info(self):
        """Compute last call date"""
        for lead in self:
            if lead.justcall_call_ids:
                lead.justcall_last_call_date = max(lead.justcall_call_ids.mapped('call_date'))
            else:
                lead.justcall_last_call_date = False

    def action_view_justcall_calls(self):
        """Open JustCall calls for this lead"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'JustCall Calls',
            'res_model': 'ptt.justcall.call',
            'view_mode': 'tree,form',
            'domain': [('lead_id', '=', self.id)],
            'context': {'default_lead_id': self.id},
        }
