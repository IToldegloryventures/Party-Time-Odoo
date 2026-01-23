# Part of Party Time Texas. See LICENSE file for full copyright and licensing details.
"""
Sale Order extension to trigger deadline calculation when project is created.

When a Sale Order is confirmed and creates a project (via Event Kickoff product),
this module automatically calculates task deadlines based on:
- sale_order.date_order (for tasks with reference='confirmation')
- sale_order.event_date (for tasks with reference='event')
"""

from odoo import models, api


class SaleOrder(models.Model):
    """Extended sale.order to trigger deadline calculation."""
    _inherit = 'sale.order'

    def action_confirm(self):
        """Override to trigger deadline calculation after project creation.

        When the sale order is confirmed:
        1. Call super() to perform standard confirmation (creates project)
        2. Find the linked project(s)
        3. Trigger deadline recalculation for all tasks
        """
        result = super().action_confirm()

        # After confirmation, recalculate deadlines for any linked projects
        for order in self:
            order._ptt_recalculate_project_deadlines()

        return result

    def _ptt_recalculate_project_deadlines(self):
        """Recalculate task deadlines for all projects linked to this SO.

        Finds projects via:
        1. Direct link: project.sale_order_id = self
        2. Via sale order lines (for products with service_tracking)
        """
        self.ensure_one()

        # Find directly linked projects
        projects = self.env['project.project'].search([
            ('sale_order_id', '=', self.id)
        ])

        # Also find projects linked via order lines
        for line in self.order_line:
            if line.project_id and line.project_id not in projects:
                projects |= line.project_id

        # Trigger deadline recalculation for each project
        for project in projects:
            project._recalculate_task_deadlines()

    def write(self, vals):
        """Override write to recalculate deadlines when event_date changes.

        If the event date is modified on a confirmed sale order,
        we need to update all task deadlines in linked projects.
        """
        result = super().write(vals)

        # If event_date changed on confirmed orders, recalculate deadlines
        if 'event_date' in vals:
            confirmed_orders = self.filtered(lambda o: o.state == 'sale')
            for order in confirmed_orders:
                order._ptt_recalculate_project_deadlines()

        return result
