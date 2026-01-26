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
