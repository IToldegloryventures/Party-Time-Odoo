# -*- coding: utf-8 -*-
# Part of Party Time Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    """
    Extends sale.order with automated CRM stage progression and event linking.
    
    Automated Workflows:
    1. When quote is sent → CRM moves to "Proposal Sent" stage
    2. When order is confirmed → CRM moves to "Booked" stage
    3. When order creates project (via service product) → Link CRM to project
    """
    _inherit = 'sale.order'

    # =========================================================================
    # EVENT TRACKING FIELDS
    # =========================================================================
    # =========================================================================
    # OVERRIDE: QUOTATION SENT
    # =========================================================================
    def action_quotation_sent(self):
        """
        Override to automatically advance CRM to 'Proposal Sent' stage.
        
        Standard Odoo behavior: Marks quote as sent, sends email
        PTT addition: Moves linked CRM opportunity to 'Proposal Sent' stage
        """
        result = super().action_quotation_sent()
        
        # Move linked CRM opportunities to "Proposal Sent" stage
        self._ptt_advance_crm_to_proposal_sent()
        
        return result

    def _ptt_advance_crm_to_proposal_sent(self):
        """Move linked CRM opportunities to 'Proposal Sent' stage."""
        proposal_sent_stage = self.env.ref(
            'ptt_business_core.stage_ptt_proposal_sent', 
            raise_if_not_found=False
        )
        
        if not proposal_sent_stage:
            return
        
        for order in self:
            if order.opportunity_id and order.opportunity_id.stage_id != proposal_sent_stage:
                # Only advance if not already at or past this stage
                if order.opportunity_id.stage_id.sequence < proposal_sent_stage.sequence:
                    order.opportunity_id.stage_id = proposal_sent_stage

    # =========================================================================
    # OVERRIDE: ORDER CONFIRMATION
    # =========================================================================
    def action_confirm(self):
        """
        Override to automatically:
        1. Advance CRM to 'Booked' stage
        2. Generate Event ID if not set
        3. Link CRM to any project created by service products
        
        Standard Odoo behavior: Confirms order, creates projects from service products
        PTT addition: CRM stage progression + project linking
        """
        # Standard confirmation (this creates projects from service products)
        result = super().action_confirm()
        
        # Move linked CRM opportunities to "Booked" stage
        self._ptt_advance_crm_to_booked()
        
        # Link CRM to any created projects
        self._ptt_link_crm_to_projects()
        
        return result

    def _ptt_advance_crm_to_booked(self):
        """Move linked CRM opportunities to 'Booked' stage."""
        booked_stage = self.env.ref(
            'crm.stage_lead4',  # Booked stage (was Won, renamed in crm_stages.xml)
            raise_if_not_found=False
        ) or self.env['crm.stage'].search([('is_won', '=', True)], limit=1)
        if not booked_stage:
            booked_stage = self.env['crm.stage'].create({
                'name': 'Booked',
                'sequence': 70,
                'is_won': True,
            })

        if not booked_stage:
            return

        for order in self:
            if order.opportunity_id and order.opportunity_id.stage_id != booked_stage:
                # Move to Booked stage (this is a "won" stage)
                order.opportunity_id.stage_id = booked_stage
                order.opportunity_id.ptt_booked = True

    def _ptt_link_crm_to_projects(self):
        """
        Link CRM opportunity to any projects created by this sale order.
        
        When a service product with "Create on Order" is confirmed, Odoo creates
        a project. This method links that project back to the CRM opportunity
        and transfers vendor estimates to project vendor assignments.
        """
        for order in self:
            if not order.opportunity_id:
                continue
            
            # Find projects created by this order's lines
            projects = order.order_line.mapped('project_id')
            
            # Also check tasks created (they link to projects)
            task_projects = order.order_line.mapped('task_id.project_id')
            projects |= task_projects
            
            for project in projects:
                if project and not project.ptt_crm_lead_id:
                    # Link project to CRM (event details are related fields - auto-populated)
                    project.write({
                        'ptt_crm_lead_id': order.opportunity_id.id,
                    })
                    
                    # Update CRM with project link (if not already set)
                    if not order.opportunity_id.ptt_project_id:
                        order.opportunity_id.ptt_project_id = project.id
                    
                    # Transfer vendor estimates to project vendor assignments
                    for estimate in order.opportunity_id.ptt_vendor_estimate_ids:
                        self.env["ptt.project.vendor.assignment"].create({
                            "project_id": project.id,
                            "service_type": estimate.service_type,
                            "estimated_cost": estimate.estimated_cost,
                            "notes": f"From CRM estimate: {estimate.vendor_name or ''}",
                        })

    # =========================================================================
    # COMPUTED FIELDS
    # =========================================================================
    ptt_guest_count = fields.Integer(
        string="PTT Guest Count",
        related='opportunity_id.ptt_guest_count',
        store=True,
        readonly=True,
        help="Guest count from the linked CRM opportunity.",
    )
    
    ptt_price_per_person = fields.Monetary(
        string="Price Per Person",
        compute='_compute_ptt_price_per_person',
        store=True,
        help="Total amount divided by guest count.",
    )

    @api.depends('amount_total', 'ptt_guest_count')
    def _compute_ptt_price_per_person(self):
        """Calculate price per person for the event."""
        for order in self:
            if order.ptt_guest_count and order.ptt_guest_count > 0:
                order.ptt_price_per_person = order.amount_total / order.ptt_guest_count
            else:
                order.ptt_price_per_person = 0.0
