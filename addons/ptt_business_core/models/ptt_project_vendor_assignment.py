import uuid
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PttProjectVendorAssignment(models.Model):
    """Actual vendor assignments and costs for projects.
    
    This model supports portal access for vendors to view their assignments,
    accept/decline work orders, and communicate via chatter.
    
    Security model:
    - Portal users can only READ their own assignments (via record rules)
    - All write operations happen through action_vendor_accept/decline methods
      which are called on sudo records from the portal controller
    """
    _name = "ptt.project.vendor.assignment"
    _description = "Project Vendor Assignment"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id desc"

    # === CORE FIELDS ===
    project_id = fields.Many2one(
        "project.project",
        string="Project",
        required=True,
        ondelete="cascade",
        index=True,
    )
    service_type = fields.Selection(
        [
            ("dj", "DJ/MC Services"),
            ("photovideo", "Photo/Video"),
            ("live_entertainment", "Live Entertainment"),
            ("lighting", "Lighting/AV"),
            ("decor", "Decor/Thematic Design"),
            ("photobooth", "Photo Booth"),
            ("caricature", "Caricature Artists"),
            ("casino", "Casino Services"),
            ("catering", "Catering"),
            ("transportation", "Transportation"),
            ("rentals", "Rentals (Other)"),
            ("staffing", "Staffing"),
            ("venue_sourcing", "Venue Sourcing"),
            ("coordination", "Event Coordination"),
            ("other", "Other"),
        ],
        string="Service Type",
        required=True,
        tracking=True,
    )
    vendor_id = fields.Many2one(
        "res.partner",
        string="Vendor",
        domain="[('x_is_vendor', '=', True)]",
        ondelete="set null",
        help="Actual vendor assigned for this service",
        tracking=True,
    )
    actual_cost = fields.Monetary(
        string="Actual Cost",
        currency_field="currency_id",
        required=True,
        help="Actual cost we pay to this vendor",
        tracking=True,
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        related="project_id.currency_id",
        readonly=True,
    )
    notes = fields.Text(string="Notes")

    # === PORTAL ACCESS TOKEN ===
    access_token = fields.Char(
        string="Access Token",
        copy=False,
        default=lambda self: str(uuid.uuid4()),
        help="Token for portal access via email links",
    )

    # === VENDOR STATUS TRACKING ===
    x_status = fields.Selection(
        [
            ("pending", "Pending"),
            ("accepted", "Accepted"),
            ("declined", "Declined"),
            ("confirmed", "Confirmed"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="pending",
        tracking=True,
        help="Track the status of this vendor assignment. 'Accepted' means vendor confirmed availability.",
    )
    x_vendor_response_date = fields.Datetime(
        string="Vendor Response Date",
        readonly=True,
        help="Date and time when vendor accepted or declined this assignment",
    )
    x_confirmed_date = fields.Date(
        string="Confirmed Date",
        help="Date when vendor confirmed their assignment",
    )

    # === VENDOR CONTACT INFO ===
    x_contact_person = fields.Char(
        string="Contact Person",
        help="Name of the contact person for this vendor assignment",
    )
    x_contact_phone = fields.Char(
        string="Contact Phone",
        help="Phone number for vendor contact person",
    )
    x_arrival_time = fields.Char(
        string="Arrival Time",
        help="Expected arrival/setup time for vendor",
    )
    x_equipment_notes = fields.Text(
        string="Equipment Notes",
        help="Notes about equipment, setup requirements, or special instructions",
    )

    # === RELATED EVENT FIELDS (for portal display) ===
    x_event_id = fields.Char(
        string="Event ID",
        related="project_id.x_event_id",
        readonly=True,
    )
    x_event_name = fields.Char(
        string="Event Name",
        related="project_id.x_event_name",
        readonly=True,
    )
    x_event_date = fields.Date(
        string="Event Date",
        related="project_id.x_event_date",
        readonly=True,
    )
    x_event_time = fields.Char(
        string="Event Time",
        related="project_id.x_event_time",
        readonly=True,
    )
    x_event_type = fields.Selection(
        string="Event Type",
        related="project_id.x_event_type",
        readonly=True,
    )
    x_venue_name = fields.Char(
        string="Venue",
        related="project_id.x_venue_name",
        readonly=True,
    )
    x_guest_count = fields.Integer(
        string="Guest Count",
        related="project_id.x_guest_count",
        readonly=True,
    )
    x_client_name = fields.Char(
        string="Client",
        related="project_id.partner_id.name",
        readonly=True,
    )

    # === COMPUTED DISPLAY FIELDS ===
    # These provide human-readable values for templates without accessing _fields
    x_service_type_display = fields.Char(
        string="Service Type (Display)",
        compute="_compute_service_type_display",
    )
    x_event_type_display = fields.Char(
        string="Event Type (Display)",
        compute="_compute_event_type_display",
    )
    x_can_respond = fields.Boolean(
        string="Can Respond",
        compute="_compute_can_respond",
        help="True if current user can accept/decline this assignment",
    )
    x_display_name = fields.Char(
        string="Display Name",
        compute="_compute_display_name",
        store=True,
    )

    @api.depends("service_type")
    def _compute_service_type_display(self):
        """Get human-readable service type label for templates."""
        service_labels = dict(self._fields["service_type"].selection)
        for rec in self:
            rec.x_service_type_display = service_labels.get(rec.service_type, rec.service_type or "")

    @api.depends("x_event_type")
    def _compute_event_type_display(self):
        """Get human-readable event type label for templates."""
        # x_event_type is a related field, get labels from project model
        try:
            event_type_field = self.env["project.project"]._fields.get("x_event_type")
            if event_type_field and hasattr(event_type_field, "selection"):
                event_labels = dict(event_type_field.selection)
            else:
                event_labels = {}
        except Exception:
            event_labels = {}
        
        for rec in self:
            rec.x_event_type_display = event_labels.get(rec.x_event_type, rec.x_event_type or "")

    @api.depends("service_type", "project_id.name", "x_event_name")
    def _compute_display_name(self):
        """Generate a display name for the assignment."""
        service_labels = dict(self._fields["service_type"].selection)
        for rec in self:
            service = service_labels.get(rec.service_type, rec.service_type or "")
            event = rec.x_event_name or rec.project_id.name or ""
            rec.x_display_name = f"{service} - {event}" if event else service

    @api.depends("vendor_id", "x_status")
    def _compute_can_respond(self):
        """Check if current user can accept/decline this assignment.
        
        User can respond if:
        - They are logged in as a portal user
        - Their partner matches the vendor_id
        - Status is still 'pending'
        
        Note: When called on a sudo record from portal controller,
        self.env.user is still the actual portal user (env is not changed).
        """
        current_partner = self.env.user.partner_id
        for rec in self:
            rec.x_can_respond = (
                rec.vendor_id
                and rec.vendor_id.id == current_partner.id
                and rec.x_status == "pending"
            )

    # === VENDOR ACTIONS ===
    def action_vendor_accept(self):
        """Accept the vendor assignment.
        
        This method is called from the portal on a sudo record.
        It validates that the current user (from env, not changed by sudo)
        is the assigned vendor before allowing the action.
        """
        self.ensure_one()
        # env.user is still the portal user even when called on sudo record
        current_partner = self.env.user.partner_id

        # Validate the vendor - security check
        if not self.vendor_id or self.vendor_id.id != current_partner.id:
            raise UserError(_("You can only accept assignments that are assigned to you."))

        if self.x_status != "pending":
            raise UserError(_("This assignment has already been responded to."))

        # Update status (happens as sudo since self is sudo)
        self.write({
            "x_status": "accepted",
            "x_vendor_response_date": fields.Datetime.now(),
            "x_confirmed_date": fields.Date.today(),
        })

        # Post a message to chatter
        self.message_post(
            body=_("Vendor <b>%s</b> has <b>accepted</b> this assignment.", self.vendor_id.name),
            message_type="notification",
            subtype_xmlid="mail.mt_note",
        )

        return True

    def action_vendor_decline(self):
        """Decline the vendor assignment.
        
        This method is called from the portal on a sudo record.
        It validates that the current user is the assigned vendor.
        """
        self.ensure_one()
        current_partner = self.env.user.partner_id

        # Validate the vendor
        if not self.vendor_id or self.vendor_id.id != current_partner.id:
            raise UserError(_("You can only decline assignments that are assigned to you."))

        if self.x_status != "pending":
            raise UserError(_("This assignment has already been responded to."))

        # Update status
        self.write({
            "x_status": "declined",
            "x_vendor_response_date": fields.Datetime.now(),
        })

        # Post a message to chatter
        self.message_post(
            body=_("Vendor <b>%s</b> has <b>declined</b> this assignment.", self.vendor_id.name),
            message_type="notification",
            subtype_xmlid="mail.mt_note",
        )

        return True

    # === OVERRIDE METHODS ===
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to generate access token and send notification when vendor is assigned."""
        # Ensure access_token is set for each record
        for vals in vals_list:
            if not vals.get("access_token"):
                vals["access_token"] = str(uuid.uuid4())
        
        records = super().create(vals_list)
        for record in records:
            if record.vendor_id:
                record._send_vendor_assignment_notification()
        return records

    def write(self, vals):
        """Override write to send notification when vendor is assigned."""
        # Track which records are getting a new vendor assignment
        records_to_notify = self.env["ptt.project.vendor.assignment"]
        if "vendor_id" in vals and vals["vendor_id"]:
            for record in self:
                # Only notify if vendor is being changed (not just updated)
                if record.vendor_id.id != vals["vendor_id"]:
                    records_to_notify |= record

        result = super().write(vals)

        # Send notifications after successful write
        for record in records_to_notify:
            record._send_vendor_assignment_notification()

        return result

    def _send_vendor_assignment_notification(self):
        """Send email notification to vendor about new assignment."""
        self.ensure_one()
        if not self.vendor_id or not self.vendor_id.email:
            return

        # Try to find and use the mail template
        template = self.env.ref(
            "ptt_business_core.mail_template_vendor_assignment",
            raise_if_not_found=False
        )
        if template:
            template.send_mail(self.id, force_send=True)
        else:
            # Fallback: post a message if template not found
            self.message_post(
                body=_(
                    "You have been assigned to provide <b>%s</b> services for the event <b>%s</b> on <b>%s</b>. "
                    "Please log in to the vendor portal to accept or decline this assignment.",
                    self.x_service_type_display or self.service_type,
                    self.x_event_name or self.project_id.name,
                    self.x_event_date or "TBD",
                ),
                partner_ids=[self.vendor_id.id],
                message_type="notification",
                subtype_xmlid="mail.mt_comment",
            )

    def get_portal_url(self):
        """Get the portal URL for this assignment (with access token for email links)."""
        self.ensure_one()
        return f"/my/vendor-assignments/{self.id}?access_token={self.access_token}"
