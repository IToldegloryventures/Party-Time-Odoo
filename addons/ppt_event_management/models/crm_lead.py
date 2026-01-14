# -*- coding: utf-8 -*-

from odoo import models, fields, api

# Selection constants used across the module
TIME_SELECTION = [
    ('09:00', '09:00 AM'),
    ('09:30', '09:30 AM'),
    ('10:00', '10:00 AM'),
    ('10:30', '10:30 AM'),
    ('11:00', '11:00 AM'),
    ('11:30', '11:30 AM'),
    ('12:00', '12:00 PM'),
    ('12:30', '12:30 PM'),
    ('13:00', '01:00 PM'),
    ('13:30', '01:30 PM'),
    ('14:00', '02:00 PM'),
    ('14:30', '02:30 PM'),
    ('15:00', '03:00 PM'),
    ('15:30', '03:30 PM'),
    ('16:00', '04:00 PM'),
    ('16:30', '04:30 PM'),
    ('17:00', '05:00 PM'),
    ('17:30', '05:30 PM'),
    ('18:00', '06:00 PM'),
    ('18:30', '06:30 PM'),
    ('19:00', '07:00 PM'),
    ('19:30', '07:30 PM'),
    ('20:00', '08:00 PM'),
    ('20:30', '08:30 PM'),
    ('21:00', '09:00 PM'),
    ('21:30', '09:30 PM'),
    ('22:00', '10:00 PM'),
]

EVENT_TYPE_SELECTION = [
    ('birthday', 'Birthday Party'),
    ('wedding', 'Wedding'),
    ('anniversary', 'Anniversary'),
    ('corporate', 'Corporate Event'),
    ('graduation', 'Graduation Party'),
    ('retirement', 'Retirement Party'),
    ('engagement', 'Engagement Party'),
    ('baby_shower', 'Baby Shower'),
    ('bridal_shower', 'Bridal Shower'),
    ('holiday', 'Holiday Party'),
    ('conference', 'Conference'),
    ('seminar', 'Seminar'),
    ('networking', 'Networking Event'),
    ('product_launch', 'Product Launch'),
    ('trade_show', 'Trade Show'),
    ('other', 'Other'),
]

EVENT_LOCATION_TYPE_SELECTION = [
    ('home', 'Home/Residence'),
    ('venue', 'Rented Venue'),
    ('restaurant', 'Restaurant'),
    ('hotel', 'Hotel'),
    ('outdoor', 'Outdoor Location'),
    ('office', 'Office/Corporate Space'),
    ('other', 'Other'),
]


class CrmLead(models.Model):
    """
    Extend CRM Lead model with event-related fields.

    This allows tracking and managing event information
    associated with customer leads and opportunities.
    """
    _inherit = 'crm.lead'

    # =====================
    # EVENT CLASSIFICATION
    # =====================
    ppt_event_type = fields.Selection(
        selection=EVENT_TYPE_SELECTION,
        string='Event Type',
        help='Type of event being planned',
        tracking=True,
    )

    ppt_event_name = fields.Char(
        string='Event Name',
        help='Name or title of the event',
        tracking=True,
    )

    ppt_event_date = fields.Date(
        string='Event Date',
        help='Planned date for the event',
        tracking=True,
    )

    ppt_event_start_time = fields.Selection(
        selection=TIME_SELECTION,
        string='Start Time',
        help='Planned start time for the event',
        tracking=True,
    )

    ppt_event_end_time = fields.Selection(
        selection=TIME_SELECTION,
        string='End Time',
        help='Planned end time for the event',
        tracking=True,
    )

    ppt_event_location_type = fields.Selection(
        selection=EVENT_LOCATION_TYPE_SELECTION,
        string='Event Location Type',
        help='Type of location where the event will be held',
        tracking=True,
    )

    ppt_venue_booked = fields.Boolean(
        string='Venue Booked',
        default=False,
        help='Is a venue already booked for this event?',
        tracking=True,
    )

    ppt_venue_name = fields.Char(
        string='Venue Name',
        help='Name of the venue if booked',
        tracking=True,
    )

    ppt_guest_count = fields.Integer(
        string='Expected Guest Count',
        default=0,
        help='Expected number of guests for the event',
        tracking=True,
    )

    ppt_total_hours = fields.Float(
        string='Event Duration (Hours)',
        default=0.0,
        help='Total duration of the event in hours',
        tracking=True,
    )
