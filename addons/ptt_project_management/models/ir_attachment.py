# Part of Party Time Texas. See LICENSE file for full copyright and licensing details.
"""
Simple attachment linking for project document management.

Based on Cybrosys project_task_attachments pattern.
Uses explicit Many2one fields with @api.model_create_multi override.

NOTE: No document categories - user confirmed simple attachment functionality only.
"""

from odoo import api, fields, models


class IrAttachment(models.Model):
    """Extended ir.attachment with project/task linking."""
    _inherit = 'ir.attachment'

    # =========================================================================
    # ATTACHMENT TARGET FIELDS (Cybrosys pattern)
    # =========================================================================
    attach_to = fields.Selection(
        selection=[
            ('project', 'Project'),
            ('task', 'Task'),
        ],
        string="Attach To",
        default='project',
        help="If Project, file attached to Project. Otherwise to Task."
    )

    project_id = fields.Many2one(
        'project.project',
        string='Project',
        help="The project this attachment belongs to",
        readonly=True,
        index=True,
    )

    task_id = fields.Many2one(
        'project.task',
        string='Task',
        help="The task this attachment belongs to",
        readonly=True,
        index=True,
    )

    # =========================================================================
    # CREATE OVERRIDE (Cybrosys pattern)
    # =========================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to link project/task based on context.

        Handles two scenarios:
        1. Creating from Documents menu with project_id/task_id in vals
        2. Creating from project/task form with res_model/res_id
        """
        for vals in vals_list:
            # Scenario 1: Creating with explicit project_id (from Documents menu)
            if vals.get('project_id') and not vals.get('task_id'):
                vals['res_id'] = vals['project_id']
                vals['res_model'] = 'project.project'
                vals['attach_to'] = 'project'

            # Scenario 2: Creating with project_id AND task_id (attach to task)
            elif vals.get('project_id') and vals.get('task_id'):
                vals['res_id'] = vals['task_id']
                vals['res_model'] = 'project.task'
                vals['attach_to'] = 'task'

            # Scenario 3: Creating from project form (res_model = project.project)
            elif not vals.get('project_id') and vals.get('res_model') == 'project.project':
                vals['project_id'] = vals.get('res_id')
                vals['attach_to'] = 'project'

            # Scenario 4: Creating from task form (res_model = project.task)
            elif not vals.get('task_id') and vals.get('res_model') == 'project.task':
                vals['task_id'] = vals.get('res_id')
                vals['attach_to'] = 'task'
                # Also link to the task's project
                if vals.get('res_id'):
                    task = self.env['project.task'].browse(vals['res_id']).exists()
                    if task and task.project_id:
                        vals['project_id'] = task.project_id.id

        return super().create(vals_list)
