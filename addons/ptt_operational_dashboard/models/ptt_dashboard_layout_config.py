from odoo import models, fields, api


class PttDashboardLayoutConfig(models.Model):
    """Dashboard Layout Configuration - Controls section positioning and layout."""
    _name = "ptt.dashboard.layout.config"
    _description = "PTT Dashboard Layout Configuration"
    _order = "sequence, id"
    _rec_name = "section_name"

    # Section identification
    section_name = fields.Char(
        string="Section Name",
        required=True,
        index=True,
        help="Unique identifier for the section (e.g., 'company_total', 'all_users')"
    )
    
    section_label = fields.Char(
        string="Display Label",
        required=True,
        help="Human-readable label for the section"
    )

    # Tab assignment
    tab_assignment = fields.Selection([
        ('sales', 'Sales Dashboard'),
        ('operations', 'Operations Dashboard'),
        ('communication', 'Communication Dashboard'),
        ('home', 'Home Tab'),
    ], string="Tab", required=True,
        help="Which dashboard tab this section belongs to"
    )

    # Positioning
    sequence = fields.Integer(
        string="Display Order",
        default=10,
        help="Order in which sections appear (lower numbers first)"
    )
    
    visible = fields.Boolean(
        string="Visible",
        default=True,
        help="Whether this section is visible"
    )

    # Layout preferences
    grid_columns = fields.Integer(
        string="Grid Columns",
        default=3,
        help="Number of columns in the grid layout for this section"
    )
    
    card_size = fields.Selection([
        ('small', 'Small'),
        ('medium', 'Medium'),
        ('large', 'Large'),
        ('full', 'Full Width'),
    ], string="Card Size", default='medium',
        help="Size of cards in this section"
    )

