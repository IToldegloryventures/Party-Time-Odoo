# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    justcall_call_ids = fields.One2many(
        'ptt.justcall.call',
        'user_id',
        string="JustCall Calls",
    )
    justcall_call_count = fields.Integer(
        string="Call Count",
        compute='_compute_justcall_call_count',
    )

    @api.depends('justcall_call_ids')
    def _compute_justcall_call_count(self):
        """Compute call count"""
        for user in self:
            user.justcall_call_count = len(user.justcall_call_ids)
