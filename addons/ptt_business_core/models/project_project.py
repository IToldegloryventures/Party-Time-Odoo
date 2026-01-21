# -*- coding: utf-8 -*-
from datetime import timedelta
from odoo import models, fields, api, _

from odoo.addons.ptt_business_core.constants import LOCATION_TYPES


class ProjectProject(models.Model):
    """Project extensions for Party Time Texas event management."""
    _inherit = "project.project"

    _sql_constraints = [
        ('unique_ptt_event_id', 'UNIQUE (ptt_event_id)', 'Event ID must be unique! Another project already has this Event ID.'),
        ('positive_ptt_guest_count', 'CHECK (ptt_guest_count >= 0)', 'Guest count cannot be negative.'),
    ]

    # =========================================================================
    # LINK TO CRM
    # =========================================================================
    ptt_crm_lead_id = fields.Many2one(
        "crm.lead",
        string="Source Opportunity",
        help="The CRM opportunity this project was created from.",
        index=True,
    )

    # =========================================================================
    # EVENT IDENTITY
    # =========================================================================
    ptt_event_id = fields.Char(
        string="PTT Event ID",
        readonly=True,
        copy=False,
        index=True,
        help="Unique event identifier (e.g., EVT-2026-0001). Links to CRM Lead, Sale Orders, Tasks.",
    )
    
    # =========================================================================
    # EVENT DETAILS - Related fields from CRM Lead (single source of truth)
    # =========================================================================
    ptt_event_type = fields.Selection(
        related="ptt_crm_lead_id.ptt_event_type",
        string="Event Type",
        store=True,
        readonly=False,
    )
    ptt_event_name = fields.Char(
        related="ptt_crm_lead_id.ptt_event_name",
        string="Event Name",
        store=True,
        readonly=False,
    )
    ptt_event_date = fields.Date(
        related="ptt_crm_lead_id.ptt_event_date",
        string="Event Date",
        store=True,
        readonly=False,
        index=True,
    )
    ptt_venue_name = fields.Char(
        related="ptt_crm_lead_id.ptt_venue_name",
        string="Venue Name",
        store=True,
        readonly=False,
    )
    ptt_venue_address = fields.Text(
        related="ptt_crm_lead_id.ptt_venue_address",
        string="Venue Address",
        store=True,
        readonly=False,
    )
    ptt_guest_count = fields.Integer(
        related="ptt_crm_lead_id.ptt_guest_count",
        string="Guest Count",
        store=True,
        readonly=False,
    )
    ptt_location_type = fields.Selection(
        related="ptt_crm_lead_id.ptt_location_type",
        string="Location Type",
        store=True,
        readonly=False,
    )
    
    # Timing fields - CRM has Float times, we convert to display
    # These pull the Float times from CRM and combine with event_date
    ptt_setup_time = fields.Float(
        related="ptt_crm_lead_id.ptt_setup_time",
        string="Setup Time",
        store=True,
        readonly=False,
    )
    ptt_event_start_time_float = fields.Float(
        related="ptt_crm_lead_id.ptt_start_time",
        string="Start Time",
        store=True,
        readonly=False,
    )
    ptt_event_end_time_float = fields.Float(
        related="ptt_crm_lead_id.ptt_end_time",
        string="End Time",
        store=True,
        readonly=False,
    )
    ptt_total_hours = fields.Float(
        related="ptt_crm_lead_id.ptt_event_duration",
        string="Total Event Hours",
        store=True,
        readonly=True,
    )
    
    # Project-only fields (not from CRM)
    ptt_setup_start_time = fields.Datetime(
        string="Setup Start (Datetime)",
        help="Computed setup start - combines event date with setup time"
    )
    ptt_event_start_time = fields.Datetime(
        string="Event Start (Datetime)",
        help="Computed event start - combines event date with start time"
    )
    ptt_event_end_time = fields.Datetime(
        string="Event End (Datetime)",
        help="Computed event end - combines event date with end time"
    )
    ptt_teardown_deadline = fields.Datetime(
        string="Teardown Deadline",
        help="When teardown must be completed - set manually on project"
    )
    
    # Vendor Notes - Project-only field (shows on work orders)
    ptt_vendor_notes = fields.Text(
        string="Vendor Notes",
        help="Notes that will appear on all vendor work orders for this event (parking, load-in instructions, etc.)"
    )

    # =========================================================================
    # VENDOR ASSIGNMENTS
    # =========================================================================
    ptt_vendor_assignment_ids = fields.One2many(
        "ptt.project.vendor.assignment",
        "project_id",
        string="Vendor Assignments",
    )
    ptt_vendor_count = fields.Integer(
        string="Vendor Count",
        compute="_compute_vendor_stats",
        store=True,
    )
    ptt_total_estimated_cost = fields.Monetary(
        string="Total Estimated Costs",
        compute="_compute_vendor_stats",
        store=True,
        currency_field="currency_id",
    )
    ptt_total_actual_cost = fields.Monetary(
        string="Total Actual Costs",
        compute="_compute_vendor_stats",
        store=True,
        currency_field="currency_id",
    )
    ptt_cost_variance = fields.Monetary(
        string="Cost Variance",
        compute="_compute_vendor_stats",
        store=True,
        currency_field="currency_id",
    )
    
    # Client financials - auto-populated from linked Sale Order
    ptt_client_total = fields.Monetary(
        string="Client Revenue",
        compute="_compute_client_total",
        store=True,
        currency_field="currency_id",
        help="Total revenue from the linked Sale Order (amount_total)",
    )
    ptt_actual_margin = fields.Monetary(
        string="Actual Margin",
        compute="_compute_vendor_stats",
        store=True,
        currency_field="currency_id",
    )
    ptt_margin_percent = fields.Float(
        string="Margin %",
        compute="_compute_vendor_stats",
        store=True,
    )

    currency_id = fields.Many2one(
        "res.currency",
        related="company_id.currency_id",
        readonly=True,
    )

    # =========================================================================
    # EVENT NOTES
    # =========================================================================
    ptt_event_notes = fields.Text(string="Event Notes")
    ptt_special_requirements = fields.Text(string="Special Requirements")
    ptt_client_preferences = fields.Text(string="Client Preferences")
    ptt_vendor_notes = fields.Text(
        string="Vendor Notes",
        help="Notes that will appear on all vendor work orders for this event"
    )

    # =========================================================================
    # COMPUTED METHODS
    # =========================================================================
    @api.depends("sale_order_id", "sale_order_id.amount_total")
    def _compute_client_total(self):
        """Compute client revenue from linked Sale Order.
        
        Automatically pulls the total from the Sale Order attached to this project.
        """
        for project in self:
            if project.sale_order_id:
                project.ptt_client_total = project.sale_order_id.amount_total
            else:
                project.ptt_client_total = 0.0

    @api.depends(
        "ptt_vendor_assignment_ids",
        "ptt_vendor_assignment_ids.estimated_cost",
        "ptt_vendor_assignment_ids.actual_cost",
        "ptt_client_total"
    )
    def _compute_vendor_stats(self):
        """Compute vendor cost statistics and profit margin.
        
        Calculates:
        - ptt_vendor_count: Number of vendor assignments
        - ptt_total_estimated_cost: Sum of estimated vendor costs
        - ptt_total_actual_cost: Sum of actual vendor costs
        - ptt_cost_variance: Actual minus estimated (negative = under budget)
        - ptt_actual_margin: Client total minus actual costs
        - ptt_margin_percent: Margin as percentage of client total
        """
        for project in self:
            assignments = project.ptt_vendor_assignment_ids
            project.ptt_vendor_count = len(assignments)
            project.ptt_total_estimated_cost = sum(assignments.mapped("estimated_cost"))
            project.ptt_total_actual_cost = sum(assignments.mapped("actual_cost"))
            project.ptt_cost_variance = project.ptt_total_actual_cost - project.ptt_total_estimated_cost
            project.ptt_actual_margin = (project.ptt_client_total or 0) - project.ptt_total_actual_cost
            if project.ptt_client_total:
                project.ptt_margin_percent = (project.ptt_actual_margin / project.ptt_client_total) * 100
            else:
                project.ptt_margin_percent = 0.0

    # =========================================================================
    # EVENT REMINDER METHODS
    # =========================================================================
    
    @api.model
    def _cron_send_event_reminders_10_day(self):
        """Cron job: Send 10-day event reminders to project managers.
        
        Finds all event projects with ptt_event_date exactly 10 days from today
        and sends reminder emails to their project managers. The 10-day mark
        is when most setup preparation happens.
        
        Called by: ir.cron ptt_cron_event_reminder_10_day
        """
        self._send_event_reminders(days_before=10)
    
    @api.model
    def _cron_send_event_reminders_3_day(self):
        """Cron job: Send 3-day urgent event reminders to project managers.
        
        Finds all event projects with ptt_event_date exactly 3 days from today
        and sends urgent reminder emails. The 3-day mark is for final
        verification and last-minute preparations.
        
        Called by: ir.cron ptt_cron_event_reminder_3_day
        """
        self._send_event_reminders(days_before=3)
    
    def _send_event_reminders(self, days_before):
        """Send event reminders for projects happening in X days.
        
        Args:
            days_before: Number of days before event to send reminder
            
        Finds projects with event date matching the target date and sends
        appropriate email template to project manager.
        """
        target_date = fields.Date.today() + timedelta(days=days_before)
        
        # Find projects with events on target date
        projects = self.search([
            ('ptt_event_date', '=', target_date),
            ('active', '=', True),
        ])
        
        if not projects:
            return
        
        # Get appropriate email template
        if days_before == 10:
            template_xmlid = 'ptt_business_core.email_template_event_reminder_10_day'
        else:
            template_xmlid = 'ptt_business_core.email_template_event_reminder_3_day'
        
        template = self.env.ref(template_xmlid, raise_if_not_found=False)
        if not template:
            # Log warning if template not found
            return
        
        for project in projects:
            # Get recipient (project manager or user)
            recipient = project.user_id
            if not recipient or not recipient.email:
                continue
            
            incomplete_tasks = project._get_incomplete_tasks()
            missing_info = project._get_missing_information()
            unconfirmed_vendors = project._get_unconfirmed_vendors()

            task_lines = []
            for task in incomplete_tasks:
                if task.date_deadline:
                    task_lines.append(f"{task.name} (due {task.date_deadline})")
                else:
                    task_lines.append(task.name)

            vendor_lines = []
            for vendor in unconfirmed_vendors:
                service = dict(vendor._fields['service_type'].selection).get(vendor.service_type, vendor.service_type)
                vendor_lines.append(f"{vendor.vendor_id.name or 'Vendor'} - {service}")

            template_ctx = {
                "ptt_missing_info": [str(info) for info in missing_info],
                "ptt_incomplete_tasks": task_lines,
                "ptt_unconfirmed_vendors": vendor_lines,
            }

            # Send email using template
            template.with_context(**template_ctx).send_mail(project.id, force_send=True)
    
    def _get_incomplete_tasks(self):
        """Get list of incomplete tasks for this project.
        
        Returns:
            Recordset of project.task records that are not done
        """
        self.ensure_one()
        return self.env['project.task'].search([
            ('project_id', '=', self.id),
            ('stage_id.fold', '=', False),  # Not in a "done" stage
        ], order='date_deadline asc')
    
    def _get_missing_information(self):
        """Get list of missing critical event information.
        
        Returns:
            List of strings describing missing information
        """
        self.ensure_one()
        missing = []
        
        if not self.ptt_venue_name:
            missing.append(_("Venue name not set"))
        if not self.ptt_venue_address:
            missing.append(_("Venue address not set"))
        if not self.ptt_event_start_time:
            missing.append(_("Event start time not set"))
        if not self.ptt_guest_count:
            missing.append(_("Guest count not set"))
        if not self.partner_id:
            missing.append(_("Client not assigned"))
        if not self.user_id:
            missing.append(_("Project manager not assigned"))
        if self.ptt_vendor_count == 0:
            missing.append(_("No vendors assigned"))
        
        return missing
    
    def _get_unconfirmed_vendors(self):
        """Get list of vendor assignments not yet confirmed.
        
        Returns:
            Recordset of ptt.project.vendor.assignment records not confirmed
        """
        self.ensure_one()
        return self.ptt_vendor_assignment_ids.filtered(
            lambda v: v.status not in ('confirmed', 'completed')
        )
