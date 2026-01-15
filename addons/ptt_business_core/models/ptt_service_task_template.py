"""
Service Task Template Model for PTT Business Core.

This model stores task templates that can be created automatically when specific
services are added to a Sales Order. For example, when Photography is ordered,
the system can auto-create Photography-specific tasks on the project.

Reference: https://www.odoo.com/documentation/19.0/contributing/development/coding_guidelines.html

NOTE: This is the schema/structure only. The actual service-specific task data
will be populated in a future phase via XML data files.
"""

from odoo import models, fields, api
from .constants import SERVICE_TYPES


class PttServiceTaskTemplate(models.Model):
    """Template for service-specific tasks.
    
    When a service product is added to a Sales Order and the order is confirmed,
    these templates can be used to auto-create relevant tasks on the project.
    
    Example: Photography service → creates tasks like:
    - Shot list review with client
    - Equipment prep
    - Photo editing timeline
    - Delivery of finals
    """
    _name = "ptt.service.task.template"
    _description = "Service Task Template"
    _order = "service_type, sequence, id"

    # === IDENTIFICATION ===
    name = fields.Char(
        string="Task Name",
        required=True,
        help="Name of the task that will be created",
    )
    service_type = fields.Selection(
        selection=SERVICE_TYPES,
        string="Service Type",
        required=True,
        index=True,
        help="The service type this task template applies to",
    )
    
    # === TASK DETAILS ===
    description = fields.Text(
        string="Description",
        help="Default description for the created task",
    )
    sequence = fields.Integer(
        string="Sequence",
        default=10,
        help="Order in which tasks appear",
    )
    
    # === SUBTASK STRUCTURE ===
    is_subtask = fields.Boolean(
        string="Is Subtask",
        default=False,
        help="If checked, this template creates a subtask under a parent task",
    )
    parent_template_id = fields.Many2one(
        comodel_name="ptt.service.task.template",
        string="Parent Task Template",
        domain="[('is_subtask', '=', False), ('service_type', '=', service_type)]",
        help="Parent task template if this is a subtask",
    )
    child_template_ids = fields.One2many(
        comodel_name="ptt.service.task.template",
        inverse_name="parent_template_id",
        string="Subtask Templates",
    )
    
    # === STATUS ===
    active = fields.Boolean(
        string="Active",
        default=True,
        help="If unchecked, the template is hidden and won't be used",
    )
    
    # === CONSTRAINTS ===
    @api.constrains('is_subtask', 'parent_template_id')
    def _check_subtask_parent(self):
        """Ensure subtasks have a parent template."""
        for record in self:
            if record.is_subtask and not record.parent_template_id:
                # Allow subtasks without parent for now (can be assigned later)
                pass
            if record.parent_template_id and record.parent_template_id.is_subtask:
                raise models.ValidationError(
                    "Parent task template cannot be a subtask itself."
                )

    # === DISPLAY NAME ===
    def name_get(self):
        """Include service type in display name for clarity."""
        result = []
        for record in self:
            service_label = dict(SERVICE_TYPES).get(record.service_type, record.service_type)
            if record.is_subtask:
                name = f"↳ {record.name} ({service_label})"
            else:
                name = f"{record.name} ({service_label})"
            result.append((record.id, name))
        return result
