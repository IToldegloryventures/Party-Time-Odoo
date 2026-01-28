# Part of Party Time Texas Event Management System
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import models


class SaleOrderLine(models.Model):
    """Extend sale.order.line (no custom project creation behavior).
    
    Project creation now relies entirely on native Odoo flows.
    """
    _inherit = 'sale.order.line'
