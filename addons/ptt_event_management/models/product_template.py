from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    ptt_is_event_service = fields.Boolean(
        string='Event Service',
        default=False,
        help='Check this box if this product is an event service that can be selected on CRM Leads',
    )
