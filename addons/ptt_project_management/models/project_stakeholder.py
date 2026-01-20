# Part of Party Time Texas Event Management System
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
"""
Project Stakeholder Model - Event Contact Directory

Simple contact directory for tracking all people involved in an event:
- Clients (the person who paid, the coordinator, bride, best POC, etc.)
- Vendors (linked to vendor assignments)

This is NOT a workflow/confirmation system - just a contact reference list.
"""

from odoo import models, fields, api

from odoo.addons.ptt_business_core.constants import SERVICE_TYPES


class ProjectStakeholder(models.Model):
    """Project Stakeholders - Event Contact Directory"""
    _name = 'project.stakeholder'
    _description = 'Project Stakeholder'
    _order = 'project_id, is_client desc, is_vendor, role'

    # =========================================================================
    # CORE FIELDS
    # =========================================================================
    project_id = fields.Many2one(
        'project.project',
        string="Project",
        required=True,
        ondelete='cascade',
        index=True,
    )
    
    partner_id = fields.Many2one(
        'res.partner',
        string="Contact",
        required=True,
        help="The contact person"
    )
    
    role = fields.Char(
        string="Role",
        help="Their role for this event (e.g., Bride, Event Coordinator, DJ, Photographer)"
    )
    
    # =========================================================================
    # STAKEHOLDER TYPE
    # =========================================================================
    is_client = fields.Boolean(
        string="Is Client",
        default=False,
        help="This person is on the client side (payer, coordinator, bride, etc.)"
    )
    
    is_vendor = fields.Boolean(
        string="Is Vendor",
        default=False,
        help="This person is a vendor providing services"
    )
    
    # Service Category for Vendors - uses SERVICE_TYPES from constants.py
    vendor_category = fields.Selection(
        selection=SERVICE_TYPES,
        string="Service Category",
        help="Type of service this vendor provides"
    )
    
    # =========================================================================
    # CONTACT INFO (Auto-populated from Contact)
    # =========================================================================
    email = fields.Char(
        related='partner_id.email',
        string="Email",
        readonly=True,
        store=True,
    )
    
    phone = fields.Char(
        related='partner_id.phone',
        string="Phone",
        readonly=True,
        store=True,
    )
    
    # =========================================================================
    # ONCHANGE - Auto-populate based on contact
    # =========================================================================
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """Auto-set vendor flag if partner is a supplier."""
        if self.partner_id:
            if self.partner_id.supplier_rank > 0:
                self.is_vendor = True
                self.is_client = False
    
    @api.onchange('is_vendor', 'vendor_category')
    def _onchange_vendor_details(self):
        """Auto-set role based on vendor category."""
        if self.is_vendor and self.vendor_category and not self.role:
            category_roles = {
                'dj': 'DJ',
                'mc': 'MC/Host',
                'band': 'Band Leader',
                'musicians': 'Musician',
                'dancers': 'Dancer',
                'characters': 'Character Performer',
                'casino': 'Casino Manager',
                'psychics': 'Psychic',
                'magicians': 'Magician',
                'comedian': 'Comedian',
                'photography': 'Photographer',
                'videography': 'Videographer',
                'photobooth': 'Photo Booth Attendant',
                'caricature_traditional': 'Traditional Caricature Artist',
                'caricature_digital': 'Digital Caricature Artist',
                'balloon_artist': 'Balloon Artist',
                'face_painters': 'Face Painter',
                'airbrush_tattoo': 'Airbrush Tattoo Artist',
                'catering': 'Caterer',
                'bartender': 'Bartender',
                'wait_staff': 'Wait Staff',
                'av_projector': 'A/V Technician',
                'av_monitor': 'A/V Technician',
                'av_led_wall': 'A/V Technician',
                'av_audio': 'A/V Technician',
                'av_misc': 'A/V Technician',
                'av_technician': 'A/V Technician',
                'av_production_mgr': 'A/V Production Manager',
                'av_technical_dir': 'A/V Technical Director',
                'balloon_decor': 'Balloon Decor Specialist',
                'furniture_rentals': 'Rental Vendor',
                'inflatables': 'Rental Vendor',
                'games': 'Rental Vendor',
                'equipment_rental': 'Rental Vendor',
                'decor': 'Decor Specialist',
                'event_planning': 'Event Planner',
                'officiant': 'Officiant',
                'petting_zoo': 'Petting Zoo Vendor',
                'deliver_setup_strike': 'Setup/Strike Crew',
                'other': 'Vendor',
            }
            self.role = category_roles.get(self.vendor_category, 'Vendor')
    
    def action_open_partner(self):
        """Open the partner form"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Contact Details',
            'res_model': 'res.partner',
            'res_id': self.partner_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
