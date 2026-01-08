# -*- coding: utf-8 -*-
"""
Public Contact Form Controller
Creates CRM leads from form submissions without requiring login.
Replicates partytimetexas.com/contact-us form fields and styling.

Reference: https://www.odoo.com/documentation/19.0/developer/howtos/website_themes/theming.html
"""
import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class ContactFormController(http.Controller):
    """Public controller for contact form - no authentication required."""

    @http.route('/contact-us', type='http', auth='public', website=True, csrf=True)
    def contact_us_page(self, **kw):
        """Render the contact us form page."""
        values = {
            'success': kw.get('success', False),
            'error': kw.get('error', False),
        }
        return request.render("ptt_contact_forms.contact_us_page", values)

    @http.route('/contact-us/submit', type='http', auth='public', website=True, methods=['POST'], csrf=True)
    def contact_us_submit(self, **kw):
        """Handle contact form submission - creates CRM lead."""
        try:
            # Validate required fields
            required_fields = {
                'name': 'Name',
                'email': 'Email',
                'phone': 'Phone',
                'event_type': 'Event Type',
                'event_location': 'Event Location',
                'event_date': 'Event Date',
                'event_time': 'Start and End Time',
                'budget': 'Estimated Budget',
                'indoor_outdoor': 'Indoor/Outdoor',
            }
            
            missing = []
            for field, label in required_fields.items():
                if not kw.get(field, '').strip():
                    missing.append(label)
            
            if missing:
                error_msg = f"Please fill in required fields: {', '.join(missing)}"
                return request.redirect(f'/contact-us?error={error_msg}')
            
            # Get the Intake stage
            intake_stage = request.env['crm.stage'].sudo().search([
                ('name', 'ilike', 'Intake')
            ], limit=1)
            
            # Build lead name
            contact_name = kw.get('name', '').strip()
            company_name = kw.get('company', '').strip()
            lead_name = f"Website Inquiry - {company_name or contact_name}"
            
            # Determine lead type based on company field
            lead_type = 'business' if company_name else 'individual'
            
            # Build description with services and details
            description_parts = []
            
            # Services of interest
            services = request.httprequest.form.getlist('services')
            if services:
                description_parts.append("**Services of Interest:**")
                for service in services:
                    description_parts.append(f"• {service}")
                description_parts.append("")
            
            # Other services
            other_services = kw.get('other_services', '').strip()
            if other_services:
                description_parts.append(f"**Other Services:** {other_services}")
                description_parts.append("")
            
            # Special requests
            special_requests = kw.get('special_requests', '').strip()
            if special_requests:
                description_parts.append(f"**Special Requests/Details:**")
                description_parts.append(special_requests)
                description_parts.append("")
            
            description_parts.append("---")
            description_parts.append("*Submitted via Website Contact Form*")
            
            # Map event type from form to CRM selection
            event_type_mapping = {
                'Anniversary': 'private_reunion',
                'Bar/Bat Mitzvah': 'private_barmitzvah',
                'Birthday (Child)': 'private_birthday',
                'Birthday (Teen)': 'private_birthday',
                'Birthday (Adult)': 'private_birthday',
                'Civic Event': 'community_cities_schools',
                'Corporate Event': 'corporate_conference',
                'Fund Raiser': 'charity_banquet',
                'Holiday Party': 'corporate_holiday',
                'School Function': 'community_cities_schools',
                'Wedding/Reception': 'private_wedding',
                'Other Event': False,
            }
            
            # Map indoor/outdoor
            indoor_outdoor_mapping = {
                'Indoors': 'indoor',
                'Outdoors': 'outdoor',
                'Not Sure': 'combination',
            }
            
            # Prepare lead values
            lead_vals = {
                'name': lead_name,
                'contact_name': contact_name,
                'partner_name': company_name or False,
                'email_from': kw.get('email', '').strip(),
                'phone': kw.get('phone', '').strip(),
                'description': '\n'.join(description_parts),
                'type': 'opportunity',
                'x_inquiry_source': 'web_form',
                'x_lead_type': lead_type,
            }
            
            # Set stage if found
            if intake_stage:
                lead_vals['stage_id'] = intake_stage.id
            
            # Event details
            event_type_form = kw.get('event_type', '').strip()
            mapped_event_type = event_type_mapping.get(event_type_form)
            if mapped_event_type:
                lead_vals['x_event_type'] = mapped_event_type
            
            # Store original event type in event name if it's "Other"
            if event_type_form == 'Other Event':
                lead_vals['x_event_name'] = 'Other Event - See Notes'
            
            # Event date
            event_date = kw.get('event_date', '').strip()
            if event_date:
                lead_vals['x_event_date'] = event_date
            
            # Event time
            event_time = kw.get('event_time', '').strip()
            if event_time:
                lead_vals['x_event_time'] = event_time
            
            # Guest count
            guest_count = kw.get('guest_count', '').strip()
            if guest_count and guest_count.isdigit():
                lead_vals['x_estimated_guest_count'] = int(guest_count)
            
            # Venue/Location
            event_location = kw.get('event_location', '').strip()
            if event_location:
                lead_vals['x_venue_name'] = event_location
            
            # Budget
            budget = kw.get('budget', '').strip()
            if budget:
                lead_vals['x_budget_range'] = budget
            
            # Indoor/Outdoor
            indoor_outdoor = kw.get('indoor_outdoor', '').strip()
            mapped_location = indoor_outdoor_mapping.get(indoor_outdoor)
            if mapped_location:
                lead_vals['x_event_location_type'] = mapped_location
            
            # Create the lead
            lead = request.env['crm.lead'].sudo().create(lead_vals)
            _logger.info("Created CRM lead #%s from contact form: %s", lead.id, lead_name)
            
            # Redirect to thank you page
            return request.redirect('/contact-us/thank-you')
            
        except Exception as e:
            _logger.error("Error creating lead from contact form: %s", str(e))
            return request.redirect('/contact-us?error=An error occurred. Please try again or call us at (214) 340-8000.')

    @http.route('/contact-us/thank-you', type='http', auth='public', website=True)
    def contact_us_thank_you(self, **kw):
        """Render thank you page after successful submission."""
        return request.render("ptt_contact_forms.contact_us_thank_you", {})
