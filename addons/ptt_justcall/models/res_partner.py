# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    justcall_call_ids = fields.One2many(
        'ptt.justcall.call',
        'partner_id',
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
        for partner in self:
            partner.justcall_call_count = len(partner.justcall_call_ids)

    @api.depends('justcall_call_ids.call_date')
    def _compute_justcall_call_info(self):
        """Compute last call date"""
        for partner in self:
            if partner.justcall_call_ids:
                partner.justcall_last_call_date = max(partner.justcall_call_ids.mapped('call_date'))
            else:
                partner.justcall_last_call_date = False

    def action_view_justcall_calls(self):
        """Open JustCall calls for this partner"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'JustCall Calls',
            'res_model': 'ptt.justcall.call',
            'view_mode': 'tree,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id},
        }
