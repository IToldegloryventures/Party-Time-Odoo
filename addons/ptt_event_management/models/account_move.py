from odoo import models, fields, api
from .crm_lead import TIME_SELECTION, EVENT_TYPE_SELECTION, EVENT_LOCATION_TYPE_SELECTION


class AccountMove(models.Model):
    _inherit = 'account.move'

    # =====================
    # EVENT OVERVIEW (Related from Sale Order)
    # =====================
    ptt_event_type = fields.Selection(
        selection=EVENT_TYPE_SELECTION,
        string='Event Type',
        compute='_compute_event_fields',
        store=True,
    )
    ptt_event_name = fields.Char(
        string='Event Name',
        compute='_compute_event_fields',
        store=True,
    )
    ptt_event_date = fields.Date(
        string='Event Date',
        compute='_compute_event_fields',
        store=True,
    )
    ptt_event_start_time = fields.Selection(
        selection=TIME_SELECTION,
        string='Start Time',
        compute='_compute_event_fields',
        store=True,
    )
    ptt_event_end_time = fields.Selection(
        selection=TIME_SELECTION,
        string='End Time',
        compute='_compute_event_fields',
        store=True,
    )
    ptt_guest_count = fields.Integer(
        related='invoice_line_ids.sale_line_ids.order_id.ptt_guest_count',
        string='Guest Count',
        store=True,
    )
    ptt_total_hours = fields.Float(
        string='Total Hours',
        compute='_compute_event_fields',
        store=True,
    )
    ptt_event_location_type = fields.Selection(
        selection=EVENT_LOCATION_TYPE_SELECTION,
        string='Event Location',
        compute='_compute_event_fields',
        store=True,
    )
    ptt_venue_booked = fields.Boolean(
        string='Event Venue (if booked)',
        compute='_compute_event_fields',
        store=True,
    )
    ptt_venue_name = fields.Char(
        string='Venue',
        compute='_compute_event_fields',
        store=True,
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

    # Helper to get related sale order
    ptt_sale_order_id = fields.Many2one(
        'sale.order',
        string='Related Sale Order',
        compute='_compute_sale_order_id',
        store=True,
    )

    # =====================
    # COMPUTED FIELDS
    # =====================
    @api.depends('invoice_line_ids.sale_line_ids.order_id')
    def _compute_sale_order_id(self):
        """Get the related sale order from invoice lines"""
        for move in self:
            sale_orders = move.invoice_line_ids.mapped('sale_line_ids.order_id')
            move.ptt_sale_order_id = sale_orders[0] if sale_orders else False

    @api.depends('ptt_sale_order_id', 'ptt_sale_order_id.ptt_event_type',
                 'ptt_sale_order_id.ptt_event_name', 'ptt_sale_order_id.ptt_event_date',
                 'ptt_sale_order_id.ptt_event_start_time', 'ptt_sale_order_id.ptt_event_end_time',
                 'ptt_sale_order_id.ptt_total_hours',
                 'ptt_sale_order_id.ptt_event_location_type', 'ptt_sale_order_id.ptt_venue_booked',
                 'ptt_sale_order_id.ptt_venue_name')
    def _compute_event_fields(self):
        """Copy event fields from related sale order"""
        for move in self:
            if move.ptt_sale_order_id:
                move.ptt_event_type = move.ptt_sale_order_id.ptt_event_type
                move.ptt_event_name = move.ptt_sale_order_id.ptt_event_name
                move.ptt_event_date = move.ptt_sale_order_id.ptt_event_date
                move.ptt_event_start_time = move.ptt_sale_order_id.ptt_event_start_time
                move.ptt_event_end_time = move.ptt_sale_order_id.ptt_event_end_time
                move.ptt_guest_count = move.ptt_sale_order_id.ptt_guest_count
                move.ptt_total_hours = move.ptt_sale_order_id.ptt_total_hours
                move.ptt_event_location_type = move.ptt_sale_order_id.ptt_event_location_type
                move.ptt_venue_booked = move.ptt_sale_order_id.ptt_venue_booked
                move.ptt_venue_name = move.ptt_sale_order_id.ptt_venue_name
            else:
                move.ptt_event_type = False
                move.ptt_event_name = False
                move.ptt_event_date = False
                move.ptt_event_start_time = False
                move.ptt_event_end_time = False
                move.ptt_guest_count = 0
                move.ptt_total_hours = 0.0
                move.ptt_event_location_type = False
                move.ptt_venue_booked = False
                move.ptt_venue_name = False

    @api.depends('amount_total', 'ptt_guest_count')
    def _compute_price_per_person(self):
        """Compute price per person = total / guest count"""
        for move in self:
            if move.ptt_guest_count and move.ptt_guest_count > 0:
                move.ptt_price_per_person = move.amount_total / move.ptt_guest_count
            else:
                move.ptt_price_per_person = 0.0
