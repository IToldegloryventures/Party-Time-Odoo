# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class JustCallUserMapping(models.Model):
    _name = 'ptt.justcall.user.mapping'
    _description = 'JustCall User to Odoo User Mapping'
    _rec_name = 'display_name'

    justcall_user_id = fields.Char(
        string="JustCall User ID",
        help="JustCall user identifier",
    )
    justcall_email = fields.Char(
        string="JustCall Email",
        required=True,
        help="Email address in JustCall",
    )
    justcall_name = fields.Char(
        string="JustCall Name",
        help="Name in JustCall",
    )
    odoo_user_id = fields.Many2one(
        'res.users',
        string="Odoo User",
        required=True,
        ondelete='cascade',
        help="Corresponding Odoo user",
    )
    active = fields.Boolean(
        string="Active",
        default=True,
    )
    display_name = fields.Char(
        string="Display Name",
        compute='_compute_display_name',
    )

    _sql_constraints = [
        ('unique_justcall_email', 'unique(justcall_email)',
         'JustCall email must be unique!'),
    ]

    @api.depends('justcall_email', 'odoo_user_id')
    def _compute_display_name(self):
        """Generate display name"""
        for mapping in self:
            parts = []
            if mapping.justcall_name:
                parts.append(mapping.justcall_name)
            if mapping.justcall_email:
                parts.append(f"({mapping.justcall_email})")
            parts.append("→")
            if mapping.odoo_user_id:
                parts.append(mapping.odoo_user_id.name)
            mapping.display_name = " ".join(parts) if parts else _("New Mapping")

    @api.constrains('justcall_email', 'odoo_user_id')
    def _check_mapping(self):
        """Validate mapping"""
        for mapping in self:
            # Check if email already exists in Odoo users
            existing_user = self.env['res.users'].search([
                ('email', '=', mapping.justcall_email),
                ('id', '!=', mapping.odoo_user_id.id),
            ], limit=1)
            if existing_user:
                raise ValidationError(
                    _("Email %s already exists for user %s. "
                      "Automatic mapping should work. Manual mapping not needed.")
                    % (mapping.justcall_email, existing_user.name)
                )
