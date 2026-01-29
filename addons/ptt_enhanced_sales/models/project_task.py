from odoo import fields, models


class ProjectTask(models.Model):
    _inherit = "project.task"

    ptt_service_product_id = fields.Many2one(
        "product.product",
        string="Service Product (Template Link)",
        help="When set on a task template, tasks are copied to the event project "
             "whenever the matching service appears on a sale order.",
    )
