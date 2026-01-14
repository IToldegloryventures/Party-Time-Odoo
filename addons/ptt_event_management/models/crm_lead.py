from odoo import models, fields, api

# Time selection options (30-minute increments)
TIME_SELECTION = [
    ('06:00', '6:00 AM'),
    ('06:30', '6:30 AM'),
    ('07:00', '7:00 AM'),
    ('07:30', '7:30 AM'),
    ('08:00', '8:00 AM'),
    ('08:30', '8:30 AM'),
    ('09:00', '9:00 AM'),
    ('09:30', '9:30 AM'),
    ('10:00', '10:00 AM'),
    ('10:30', '10:30 AM'),
    ('11:00', '11:00 AM'),
    ('11:30', '11:30 AM'),
    ('12:00', '12:00 PM'),
    ('12:30', '12:30 PM'),
    ('13:00', '1:00 PM'),
    ('13:30', '1:30 PM'),
    ('14:00', '2:00 PM'),
    ('14:30', '2:30 PM'),
    ('15:00', '3:00 PM'),
    ('15:30', '3:30 PM'),
    ('16:00', '4:00 PM'),
    ('16:30', '4:30 PM'),
    ('17:00', '5:00 PM'),
    ('17:30', '5:30 PM'),
    ('18:00', '6:00 PM'),
    ('18:30', '6:30 PM'),
    ('19:00', '7:00 PM'),
    ('19:30', '7:30 PM'),
    ('20:00', '8:00 PM'),
    ('20:30', '8:30 PM'),
    ('21:00', '9:00 PM'),
    ('21:30', '9:30 PM'),
    ('22:00', '10:00 PM'),
    ('22:30', '10:30 PM'),
    ('23:00', '11:00 PM'),
    ('23:30', '11:30 PM'),
    ('00:00', '12:00 AM'),
]

EVENT_TYPE_SELECTION = [
    ('wedding', 'Wedding'),
    ('corporate', 'Corporate Event'),
    ('birthday', 'Birthday Party'),
    ('anniversary', 'Anniversary'),
    ('graduation', 'Graduation'),
    ('holiday', 'Holiday Party'),
    ('fundraiser', 'Fundraiser/Gala'),
    ('school', 'School Event'),
    ('quinceañera', 'Quinceañera'),
    ('bar_bat_mitzvah', 'Bar/Bat Mitzvah'),
    ('reunion', 'Reunion'),
    ('retirement', 'Retirement Party'),
    ('baby_shower', 'Baby Shower'),
    ('bridal_shower', 'Bridal Shower'),
    ('other', 'Other'),
]

EVENT_LOCATION_TYPE_SELECTION = [
    ('indoor', 'Indoor'),
    ('outdoor', 'Outdoor'),
    ('both', 'Indoor & Outdoor'),
    ('tbd', 'TBD'),
]


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    # =====================
    # EVENT OVERVIEW
    # =====================
    ptt_event_type = fields.Selection(
        selection=EVENT_TYPE_SELECTION,
        string='Event Type',
    )
    ptt_event_specific_goal = fields.Char(
        string='Specific Goal',
        help='What is the specific goal or theme of this event?',
    )
    ptt_event_name = fields.Char(
        string='Event Name',
        help='Name of the event (if known)',
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
    
    # Renamed from ptt_estimated_guest_count
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
    # SERVICES REQUESTED
    # =====================
    ptt_requested_service_ids = fields.Many2many(
        'product.product',
        'crm_lead_product_rel',
        'lead_id',
        'product_id',
        string='Services Requested',
        domain="[('ptt_is_event_service', '=', True)]",
        help='Select the services the client is interested in',
    )

    # =====================
    # COMPUTED FIELDS
    # =====================
    @api.depends('ptt_event_start_time', 'ptt_event_end_time')
    def _compute_total_hours(self):
        """Compute total hours between start and end time"""
        for lead in self:
            if lead.ptt_event_start_time and lead.ptt_event_end_time:
                # Parse start time (HH:MM format)
                start_parts = lead.ptt_event_start_time.split(':')
                start_hours = int(start_parts[0]) + int(start_parts[1]) / 60.0
                
                # Parse end time (HH:MM format)
                end_parts = lead.ptt_event_end_time.split(':')
                end_hours = int(end_parts[0]) + int(end_parts[1]) / 60.0
                
                # Handle times that cross midnight
                if end_hours < start_hours:
                    end_hours += 24
                
                lead.ptt_total_hours = end_hours - start_hours
            else:
                lead.ptt_total_hours = 0.0

    # =====================
    # ACTIONS
    # =====================
    def action_create_quotation_with_services(self):
        """Create a quotation and auto-populate with selected services"""
        self.ensure_one()
        
        # Create the sale order
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner_id.id,
            'opportunity_id': self.id,
            # Copy event overview fields
            'ptt_event_type': self.ptt_event_type,
            'ptt_event_name': self.ptt_event_name,
            'ptt_event_date': self.ptt_event_date,
            'ptt_event_start_time': self.ptt_event_start_time,
            'ptt_event_end_time': self.ptt_event_end_time,
            'ptt_guest_count': self.ptt_guest_count,
            'ptt_event_location_type': self.ptt_event_location_type,
            'ptt_venue_booked': self.ptt_venue_booked,
            'ptt_venue_name': self.ptt_venue_name,
        })
        
        # Add order lines for each requested service (price = 0, to be filled by sales rep)
        for product in self.ptt_requested_service_ids:
            self.env['sale.order.line'].create({
                'order_id': sale_order.id,
                'product_id': product.id,
                'product_uom_qty': 1,
                'price_unit': 0.0,  # Sales rep fills in price
            })
        
        # Open the new sale order
        return {
            'type': 'ir.actions.act_window',
            'name': 'Quotation',
            'res_model': 'sale.order',
            'res_id': sale_order.id,
            'view_mode': 'form',
            'target': 'current',
        }
