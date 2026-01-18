# Part of Party Time Texas Event Management System
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def write(self, vals):
        res = super().write(vals)
        if "payment_state" in vals:
            paid_invoices = self.filtered(
                lambda move: move.move_type == "out_invoice"
                and move.state == "posted"
                and move.payment_state == "paid"
            )
            if paid_invoices:
                orders = paid_invoices.invoice_line_ids.sale_line_ids.order_id
                if orders:
                    orders._update_crm_stage_on_payment_confirmed()
        return res
