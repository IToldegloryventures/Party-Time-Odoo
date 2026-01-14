# -*- coding: utf-8 -*-

from odoo import models, fields, api
from .crm_lead import (
    TIME_SELECTION,
    EVENT_TYPE_SELECTION,
    EVENT_LOCATION_TYPE_SELECTION,
)


class AccountMove(models.Model):
    """
    Extend account.move model with event-related fields.
    
    This allows invoices to display and track event information
    automatically synchronized from related sale orders.
    """
    _inherit = 'account.move'

    # =====================
    # EVENT OVERVIEW (Related from Sale Order)
    # =====================
    ppt_event_type = fields.Selection(
        selection=EVENT_TYPE_SELECTION,
        string='Event Type',
        compute='_compute_event_fields',
        store=True,
        help='Type of event associated with this invoice',
    )
    
    ppt_event_name = fields.Char(
        string='Event Name',
        compute='_compute_event_fields',
        store=True,
        help='Name of the event associated with this invoice',
    )
    
    ppt_event_date = fields.Date(
        string='Event Date',
        compute='_compute_event_fields',
        store=True,
        help='Date when the event is scheduled',
    )
    
    ppt_event_start_time = fields.Selection(
        selection=TIME_SELECTION,
        string='Start Time',
        compute='_compute_event_fields',
        store=True,
        help='Event start time',
    )
    
    ppt_event_end_time = fields.Selection(
        selection=TIME_SELECTION,
        string='End Time',
        compute='_compute_event_fields',
        store=True,
        help='Event end time',
    )
    
    ppt_guest_count = fields.Integer(
        string='Guest Count',
        related='invoice_line_ids.sale_line_ids.order_id.ppt_guest_count',
        store=True,
        help='Total number of guests for the event',
    )
    
    ppt_total_hours = fields.Float(
        string='Total Hours',
        compute='_compute_event_fields',
        store=True,
        help='Duration of the event in hours',
    )
    
    ppt_event_location_type = fields.Selection(
        selection=EVENT_LOCATION_TYPE_SELECTION,
        string='Event Location',
        compute='_compute_event_fields',
        store=True,
        help='Type of location where the event is held',
    )
    
    ppt_venue_booked = fields.Boolean(
        string='Event Venue (if booked)',
        compute='_compute_event_fields',
        store=True,
        help='Whether a specific venue is booked for this event',
    )
    
    ppt_venue_name = fields.Char(
        string='Venue',
        compute='_compute_event_fields',
        store=True,
        help='Name of the venue where the event is held',
    )

    # =====================
    # COMPUTED PRICE PER PERSON
    # =====================
    ppt_price_per_person = fields.Monetary(
        string='Price Per Person',
        compute='_compute_price_per_person',
        store=True,
        currency_field='currency_id',
        help='Total amount divided by guest count',
    )

    # =====================
    # HELPER FIELDS
    # =====================
    ppt_sale_order_id = fields.Many2one(
        'sale.order',
        string='Related Sale Order',
        compute='_compute_sale_order_id',
        store=True,
        help='Sale order linked to this invoice',
    )

    # =====================
    # COMPUTED FIELDS
    # =====================
    @api.depends('invoice_line_ids.sale_line_ids.order_id')
    def _compute_sale_order_id(self):
        """
        Get the related sale order from invoice lines.
        
        Retrieves the first sale order associated with any of the
        invoice lines, if available.
        """
        for move in self:
            sale_orders = move.invoice_line_ids.mapped('sale_line_ids.order_id')
            move.ppt_sale_order_id = sale_orders[0] if sale_orders else False

    @api.depends(
        'ppt_sale_order_id',
        'ppt_sale_order_id.ppt_event_type',
        'ppt_sale_order_id.ppt_event_name',
        'ppt_sale_order_id.ppt_event_date',
        'ppt_sale_order_id.ppt_event_start_time',
        'ppt_sale_order_id.ppt_event_end_time',
        'ppt_sale_order_id.ppt_total_hours',
        'ppt_sale_order_id.ppt_event_location_type',
        'ppt_sale_order_id.ppt_venue_booked',
        'ppt_sale_order_id.ppt_venue_name',
    )
    def _compute_event_fields(self):
        """
        Copy event fields from related sale order.
        
        Automatically synchronizes event information from the related
        sale order to the invoice. If no sale order is related, all
        fields are cleared.
        """
        for move in self:
            if move.ppt_sale_order_id:
                move.ppt_event_type = move.ppt_sale_order_id.ppt_event_type
                move.ppt_event_name = move.ppt_sale_order_id.ppt_event_name
                move.ppt_event_date = move.ppt_sale_order_id.ppt_event_date
                move.ppt_event_start_time = (
                    move.ppt_sale_order_id.ppt_event_start_time
                )
                move.ppt_event_end_time = move.ppt_sale_order_id.ppt_event_end_time
                move.ppt_total_hours = move.ppt_sale_order_id.ppt_total_hours
                move.ppt_event_location_type = (
                    move.ppt_sale_order_id.ppt_event_location_type
                )
                move.ppt_venue_booked = move.ppt_sale_order_id.ppt_venue_booked
                move.ppt_venue_name = move.ppt_sale_order_id.ppt_venue_name
            else:
                move.ppt_event_type = False
                move.ppt_event_name = False
                move.ppt_event_date = False
                move.ppt_event_start_time = False
                move.ppt_event_end_time = False
                move.ppt_total_hours = 0.0
                move.ppt_event_location_type = False
                move.ppt_venue_booked = False
                move.ppt_venue_name = False

    @api.depends('amount_total', 'ppt_guest_count')
    def _compute_price_per_person(self):
        """
        Compute price per person = total / guest count.
        
        Calculates the per-person cost by dividing the total invoice
        amount by the number of guests. Returns 0.0 if guest count
        is not set or is zero.
        """
        for move in self:
            if move.ppt_guest_count and move.ppt_guest_count > 0:
                move.ppt_price_per_person = (
                    move.amount_total / move.ppt_guest_count
                )
            else:
                move.ppt_price_per_person = 0.0
