# -*- coding: utf-8 -*-
# Part of Party Time Texas. See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class ResUsers(models.Model):
    """Extend res.users to add PTT operational dashboard homepage option."""

    _inherit = "res.users"

    ptt_dashboard_as_homepage = fields.Boolean(
        string="Use PTT Dashboard as Homepage",
        default=False,
        help="If enabled, the PTT Operational Dashboard will be your default homepage "
        "instead of the standard Apps menu.",
    )
