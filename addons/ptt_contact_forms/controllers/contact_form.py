# -*- coding: utf-8 -*-
"""
Public Contact Form Controller
Creates CRM leads from form submissions without requiring login.

Brand: Black #040303, Gold #D4BF91, Red #A4031F, Gray #B2B4B3
Font: Open Sans

Use ?embed=1 for WordPress iframe integration (hides header/footer)
"""
import logging
import html
import re
from datetime import datetime
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
            'embed': kw.get('embed', False),  # For WordPress iframe
        }
        return request.render("ptt_contact_forms.contact_us_page", values)

    @http.route('/contact-us/submit', type='http', auth='public', website=True, methods=['POST'], csrf=True)
    def contact_us_submit(self, **kw):
        """Handle contact form submission - creates CRM lead."""
        embed = kw.get('embed', '')
        embed_param = '?embed=1' if embed else ''
        
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
                error_msg = f"Please fill in: {', '.join(missing)}"
                return request.redirect(f'/contact-us{embed_param}&error={error_msg}' if embed_param else f'/contact-us?error={error_msg}')
            
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
            
            # Get form data (will be used for both description and customer notes)
            services = request.httprequest.form.getlist('services')
            event_type_form = kw.get('event_type', '').strip()
            event_date = kw.get('event_date', '').strip()
            event_time = kw.get('event_time', '').strip()
            event_location = kw.get('event_location', '').strip()
            guest_count = kw.get('guest_count', '').strip()
            budget = kw.get('budget', '').strip()
            indoor_outdoor = kw.get('indoor_outdoor', '').strip()
            special_requests = kw.get('special_requests', '').strip()
            
            # Build description with services and details (for backward compatibility)
            description_parts = []
            
            # Services of interest
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
            if special_requests:
                description_parts.append("**Special Requests/Details:**")
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
            
            # Prepare CORE lead values (standard Odoo fields - always work)
            lead_vals = {
                'name': lead_name,
                'contact_name': contact_name,
                'partner_name': company_name or False,
                'email_from': kw.get('email', '').strip(),
                'phone': kw.get('phone', '').strip(),
                'description': '\n'.join(description_parts),
                'type': 'opportunity',
            }
            
            # Set stage if found
            if intake_stage:
                lead_vals['stage_id'] = intake_stage.id
            
            _logger.info("Creating CRM lead with core values: %s", lead_vals)
            
            # Create the lead FIRST with core fields
            lead = request.env['crm.lead'].sudo().create(lead_vals)
            _logger.info("Created CRM lead #%s from contact form: %s", lead.id, lead_name)
            
            # NOW update with custom PTT fields (these may not exist if ptt_business_core not installed)
            try:
                custom_vals = {}
                
                # Use standard Odoo source_id for lead source tracking
                # Look for or create a "Website Form" source
                try:
                    website_source = request.env['utm.source'].sudo().search([
                        ('name', '=', 'Website Contact Form')
                    ], limit=1)
                    if not website_source:
                        website_source = request.env['utm.source'].sudo().create({
                            'name': 'Website Contact Form'
                        })
                    if website_source:
                        lead.sudo().write({'source_id': website_source.id})
                except Exception:
                    pass  # utm.source may not be available
                
                # Event details - map to PTT custom fields
                mapped_event_type = event_type_mapping.get(event_type_form)
                if mapped_event_type:
                    custom_vals['x_event_type'] = mapped_event_type
                
                # Event date
                if event_date:
                    custom_vals['x_event_date'] = event_date
                
                # Event time
                if event_time:
                    custom_vals['x_event_time'] = event_time
                
                # Guest count
                if guest_count and guest_count.isdigit():
                    custom_vals['x_estimated_guest_count'] = int(guest_count)
                
                # Venue/Location
                if event_location:
                    custom_vals['x_venue_name'] = event_location
                
                # Budget - use standard expected_revenue if numeric, otherwise store in description
                if budget:
                    # Try to extract numeric value from budget string
                    budget_match = re.search(r'[\d,]+', budget.replace(',', ''))
                    if budget_match:
                        try:
                            # Use the first number found as expected revenue
                            budget_num = float(budget_match.group().replace(',', ''))
                            lead.sudo().write({'expected_revenue': budget_num})
                        except (ValueError, TypeError):
                            pass
                
                # Indoor/Outdoor
                mapped_location = indoor_outdoor_mapping.get(indoor_outdoor)
                if mapped_location:
                    custom_vals['x_event_location_type'] = mapped_location
                
                # Build HTML for customer submission notes
                # Services appear as TEXT only (not mapped to boolean fields)
                try:
                    # Escape user input for security
                    safe_event_type = html.escape(event_type_form) if event_type_form else 'Not specified'
                    safe_event_date = html.escape(event_date) if event_date else 'Not specified'
                    safe_event_time = html.escape(event_time) if event_time else 'Not specified'
                    safe_event_location = html.escape(event_location) if event_location else 'Not specified'
                    safe_guest_count = html.escape(guest_count) if guest_count else 'Not specified'
                    safe_budget = html.escape(budget) if budget else 'Not specified'
                    safe_indoor_outdoor = html.escape(indoor_outdoor) if indoor_outdoor else 'Not specified'
                    safe_special_requests = html.escape(special_requests) if special_requests else ''
                    
                    # Format services as HTML list (TEXT ONLY - not mapped to fields)
                    services_html = ''
                    if services:
                        services_html = '<ul>' + ''.join([f'<li>{html.escape(service)}</li>' for service in services]) + '</ul>'
                    else:
                        services_html = '<p><em>None selected</em></p>'
                    
                    # Build customer notes HTML
                    submission_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    customer_notes_html = f"""
<div class="ptt-customer-notes">
    <h3>Form Submission Details</h3>
    <p><strong>Submitted:</strong> {submission_time}</p>
    
    <h4>Event Information</h4>
    <ul>
        <li><strong>Event Type:</strong> {safe_event_type}</li>
        <li><strong>Event Date:</strong> {safe_event_date}</li>
        <li><strong>Event Time:</strong> {safe_event_time}</li>
        <li><strong>Location:</strong> {safe_event_location}</li>
        <li><strong>Guest Count:</strong> {safe_guest_count}</li>
        <li><strong>Budget:</strong> {safe_budget}</li>
        <li><strong>Setting:</strong> {safe_indoor_outdoor}</li>
    </ul>
    
    <h4>Services of Interest (Customer Selection)</h4>
    {services_html}
    
    {f'<h4>Special Requests</h4><p>{safe_special_requests}</p>' if safe_special_requests else ''}
</div>
"""
                    custom_vals['x_customer_submission_notes'] = customer_notes_html.strip()
                except Exception as html_err:
                    _logger.warning("Could not build customer notes HTML for lead #%s: %s", lead.id, str(html_err))
                
                # Update the lead with custom fields
                if custom_vals:
                    lead.sudo().write(custom_vals)
                    _logger.info("Updated CRM lead #%s with PTT custom fields", lead.id)
                    
            except Exception as custom_err:
                _logger.warning("Could not set custom PTT fields on lead #%s: %s", lead.id, str(custom_err))
            
            # Redirect to thank you page
            return request.redirect(f'/contact-us/thank-you{embed_param}')
            
        except Exception as e:
            _logger.error("Error creating lead from contact form: %s", str(e))
            error_url = f'/contact-us{embed_param}&error=An error occurred. Please try again or call us at (214) 340-8000.' if embed_param else '/contact-us?error=An error occurred. Please try again or call us at (214) 340-8000.'
            return request.redirect(error_url)

    @http.route('/contact-us/thank-you', type='http', auth='public', website=True)
    def contact_us_thank_you(self, **kw):
        """Render thank you page after successful submission."""
        values = {
            'embed': kw.get('embed', False),
        }
        return request.render("ptt_contact_forms.contact_us_thank_you", values)
