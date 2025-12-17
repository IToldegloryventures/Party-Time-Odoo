from odoo import models, fields, api


class ProjectProject(models.Model):
    _inherit = "project.project"

    # Link back to source CRM Lead
    x_crm_lead_id = fields.Many2one(
        "crm.lead",
        string="Source Opportunity",
        help="The CRM opportunity this project was created from.",
        index=True,
    )

    # Core event identity
    x_event_id = fields.Char(string="Event ID")
    x_event_type = fields.Selection(
        selection=lambda self: self.env["crm.lead"]._fields["x_event_type"].selection,
        string="Event Type",
        help="Copied from the related opportunity / lead.",
    )
    x_event_name = fields.Char(string="Event Name")
    x_event_date = fields.Date(string="Event Date")
    x_event_time = fields.Char(string="Event Time")
    x_guest_count = fields.Integer(string="Guest Count")
    x_venue_name = fields.Char(string="Venue")

    # Schedule
    x_setup_start_time = fields.Char(string="Setup Start Time")
    x_event_start_time = fields.Char(string="Event Start Time")
    x_event_end_time = fields.Char(string="Event End Time")
    x_total_hours = fields.Float(string="Total Hours")
    x_teardown_deadline = fields.Char(string="Tear-Down Deadline")

    # Event details
    x_theme_dress_code = fields.Text(string="Theme, Dress Code, or Style Preference")
    x_special_requirements_desc = fields.Text(string="Special Requirements")
    x_inclement_weather_plan = fields.Text(string="Inclement Weather Plan")
    x_parking_restrictions_desc = fields.Text(string="Parking/Delivery Restrictions")


