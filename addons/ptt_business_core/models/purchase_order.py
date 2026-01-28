# -*- coding: utf-8 -*-
# Part of Party Time Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    ptt_project_id = fields.Many2one(
        "project.project",
        string="Event Project",
        help="Project linked to this purchase order.",
    )
    ptt_event_id = fields.Char(
        string="Event ID",
        related="ptt_project_id.ptt_event_id",
        store=True,
        readonly=True,
        help="Event ID from the linked project. Used to track event across CRM, Sales, Projects, and Tasks.",
    )
