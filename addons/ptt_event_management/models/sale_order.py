from odoo import models, fields, api
from .crm_lead import TIME_SELECTION, EVENT_TYPE_SELECTION, EVENT_LOCATION_TYPE_SELECTION


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # =====================
    # EVENT OVERVIEW
    # =====================
    ptt_event_type = fields.Selection(
        selection=EVENT_TYPE_SELECTION,
        string='Event Type',
    )
    ptt_event_name = fields.Char(
        string='Event Name',
    )
    ptt_event_date = fields.Date(
        string='Event Date',
    )
    ptt_event_start_time = fields.Selection(
        selection=TIME_SELECTION,
        string='Start Time',
    )
    ptt_event_end_time = fields.Selection(
        selection=TIME_SELECTION,
        string='End Time',
    )
    ptt_guest_count = fields.Integer(
        string='Guest Count',
    )
    ptt_total_hours = fields.Float(
        string='Total Hours',
        compute='_compute_total_hours',
        store=True,
    )
    ptt_event_location_type = fields.Selection(
        selection=EVENT_LOCATION_TYPE_SELECTION,
        string='Event Location',
    )
    ptt_venue_booked = fields.Boolean(
        string='Event Venue (if booked)',
    )
    ptt_venue_name = fields.Char(
        string='Venue',
    )

    # =====================
    # COMPUTED PRICE PER PERSON
    # =====================
    ptt_price_per_person = fields.Monetary(
        string='Price Per Person',
        compute='_compute_price_per_person',
        store=True,
        currency_field='currency_id',
        help='Total amount divided by guest count',
    )

    # =====================
    # COMPUTED FIELDS
    # =====================
    @api.depends('ptt_event_start_time', 'ptt_event_end_time')
    def _compute_total_hours(self):
        """Compute total hours between start and end time"""
        for order in self:
            if order.ptt_event_start_time and order.ptt_event_end_time:
                # Parse start time (HH:MM format)
                start_parts = order.ptt_event_start_time.split(':')
                start_hours = int(start_parts[0]) + int(start_parts[1]) / 60.0
                
                # Parse end time (HH:MM format)
                end_parts = order.ptt_event_end_time.split(':')
                end_hours = int(end_parts[0]) + int(end_parts[1]) / 60.0
                
                # Handle times that cross midnight
                if end_hours < start_hours:
                    end_hours += 24
                
                order.ptt_total_hours = end_hours - start_hours
            else:
                order.ptt_total_hours = 0.0

    @api.depends('amount_total', 'ptt_guest_count')
    def _compute_price_per_person(self):
        """Compute price per person = total / guest count"""
        for order in self:
            if order.ptt_guest_count and order.ptt_guest_count > 0:
                order.ptt_price_per_person = order.amount_total / order.ptt_guest_count
            else:
                order.ptt_price_per_person = 0.0

    # =====================
    # ONCHANGE - Copy from Lead
    # =====================
    @api.onchange('opportunity_id')
    def _onchange_opportunity_id_event_fields(self):
        """Copy event fields from CRM Lead when opportunity is selected"""
        if self.opportunity_id:
            self.ptt_event_type = self.opportunity_id.ptt_event_type
            self.ptt_event_name = self.opportunity_id.ptt_event_name
            self.ptt_event_date = self.opportunity_id.ptt_event_date
            self.ptt_event_start_time = self.opportunity_id.ptt_event_start_time
            self.ptt_event_end_time = self.opportunity_id.ptt_event_end_time
            self.ptt_guest_count = self.opportunity_id.ptt_guest_count
            self.ptt_event_location_type = self.opportunity_id.ptt_event_location_type
            self.ptt_venue_booked = self.opportunity_id.ptt_venue_booked
            self.ptt_venue_name = self.opportunity_id.ptt_venue_name
