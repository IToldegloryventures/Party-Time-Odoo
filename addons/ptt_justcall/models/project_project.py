# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ProjectProject(models.Model):
    _inherit = 'project.project'

    justcall_call_ids = fields.One2many(
        'ptt.justcall.call',
        'project_id',
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
        for project in self:
            project.justcall_call_count = len(project.justcall_call_ids)

    @api.depends('justcall_call_ids.call_date')
    def _compute_justcall_call_info(self):
        """Compute last call date"""
        for project in self:
            if project.justcall_call_ids:
                project.justcall_last_call_date = max(project.justcall_call_ids.mapped('call_date'))
            else:
                project.justcall_last_call_date = False

    def action_view_justcall_calls(self):
        """Open JustCall calls for this project"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'JustCall Calls',
            'res_model': 'ptt.justcall.call',
            'view_mode': 'tree,form',
            'domain': [('project_id', '=', self.id)],
            'context': {'default_project_id': self.id},
        }
