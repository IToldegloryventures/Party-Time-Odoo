"""
Vendor Portal Controller - Work Order Access + Vendor Application

Reference: https://www.odoo.com/documentation/19.0/developer/reference/backend/http.html
"""
import base64
import logging

from odoo import http, fields, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.exceptions import AccessError

_logger = logging.getLogger(__name__)


class VendorPortal(CustomerPortal):
    """Extend portal for vendor work order access and vendor application."""
    
    def _prepare_home_portal_values(self, counters):
        """Add work order count and application count to portal home."""
        values = super()._prepare_home_portal_values(counters)
        
        partner = request.env.user.partner_id
        Assignment = request.env['ptt.project.vendor.assignment']
        today = fields.Date.today()
        
        if 'work_order_count' in counters:
            domain = [('vendor_id', '=', partner.id)]
            try:
                count = Assignment.search_count(domain) \
                    if Assignment.check_access_rights('read', raise_exception=False) else 0
            except Exception:
                count = 0
            values['work_order_count'] = count
        
        # Upcoming events count (accepted assignments with future event dates)
        if 'upcoming_event_count' in counters:
            try:
                count = Assignment.sudo().search_count([
                    ('vendor_id', '=', partner.id),
                    ('status', '=', 'confirmed'),
                    ('event_date', '>=', today),
                ])
            except Exception:
                count = 0
            values['upcoming_event_count'] = count
        
        # Task count
        if 'vendor_task_count' in counters:
            try:
                count = request.env['ptt.vendor.task'].sudo().search_count([
                    ('vendor_id', '=', partner.id),
                    ('state', 'in', ['todo', 'in_progress']),
                ])
            except Exception:
                count = 0
            values['vendor_task_count'] = count
        
        # Add vendor application count
        if 'application_count' in counters:
            try:
                # Find all vendor records this user created or is portal user for
                domain = [
                    '|',
                    ('ptt_portal_user_id', '=', request.env.user.id),
                    ('create_uid', '=', request.env.user.id),
                    ('supplier_rank', '>', 0),
                ]
                count = request.env['res.partner'].sudo().search_count(domain)
            except Exception:
                count = 0
            values['application_count'] = count
        
        # Add RFQ count for vendors
        if 'rfq_count' in counters:
            try:
                count = request.env['ptt.vendor.rfq'].sudo().search_count([
                    ('vendor_ids', 'in', partner.ids),
                    ('state', 'not in', ['draft']),
                ])
            except Exception:
                count = 0
            values['rfq_count'] = count
        
        return values
    
    @http.route(['/my/work-orders', '/my/work-orders/page/<int:page>'], 
                type='http', auth="user", website=True)
    def portal_my_work_orders(self, page=1, sortby=None, filterby=None, **kw):
        """Display vendor's work orders list."""
        values = self._prepare_portal_layout_values()
        Assignment = request.env['ptt.project.vendor.assignment']
        partner = request.env.user.partner_id
        today = fields.Date.today()
        
        domain = [('vendor_id', '=', partner.id)]
        
        # Sorting
        searchbar_sortings = {
            'date': {'label': _('Event Date'), 'order': 'event_date desc'},
            'name': {'label': _('Event Name'), 'order': 'project_id asc'},
            'status': {'label': _('Status'), 'order': 'status asc'},
        }
        
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']
        
        # Filters
        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
            'upcoming': {'label': _('Upcoming'), 'domain': [('status', '=', 'confirmed'), ('event_date', '>=', today)]},
            'past': {'label': _('Past'), 'domain': [('event_date', '<', today)]},
            'pending': {'label': _('Pending Response'), 'domain': [('status', '=', 'pending')]},
            'confirmed': {'label': _('Accepted'), 'domain': [('status', '=', 'confirmed')]},
            'completed': {'label': _('Completed'), 'domain': [('status', '=', 'completed')]},
        }
        
        if not filterby:
            filterby = 'all'
        domain += searchbar_filters[filterby]['domain']
        
        # Count and paginate
        count = Assignment.search_count(domain)
        pager_values = portal_pager(
            url="/my/work-orders",
            url_args={'sortby': sortby, 'filterby': filterby},
            total=count,
            page=page,
            step=10
        )
        
        assignments = Assignment.search(
            domain, 
            limit=10,
            offset=pager_values['offset'],
            order=order,
        )
        
        values.update({
            'assignments': assignments,
            'pager': pager_values,
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'searchbar_filters': searchbar_filters,
            'filterby': filterby,
            'page_name': 'work_orders',
        })
        
        return request.render("ptt_vendor_management.portal_my_work_orders", values)
    
    @http.route(['/my/upcoming-events'], type='http', auth="user", website=True)
    def portal_upcoming_events(self, **kw):
        """Display vendor's upcoming confirmed events."""
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        today = fields.Date.today()
        
        assignments = request.env['ptt.project.vendor.assignment'].sudo().search([
            ('vendor_id', '=', partner.id),
            ('status', '=', 'confirmed'),
            ('event_date', '>=', today),
        ], order='event_date asc')
        
        values.update({
            'assignments': assignments,
            'page_name': 'upcoming_events',
        })
        
        return request.render("ptt_vendor_management.portal_upcoming_events", values)
    
    @http.route(['/my/vendor-tasks', '/my/vendor-tasks/page/<int:page>'], 
                type='http', auth="user", website=True)
    def portal_vendor_tasks(self, page=1, filterby=None, **kw):
        """Display vendor's assigned tasks."""
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        
        domain = [('vendor_id', '=', partner.id)]
        
        # Filters
        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
            'todo': {'label': _('To Do'), 'domain': [('state', '=', 'todo')]},
            'in_progress': {'label': _('In Progress'), 'domain': [('state', '=', 'in_progress')]},
            'done': {'label': _('Completed'), 'domain': [('state', '=', 'done')]},
        }
        
        if not filterby:
            filterby = 'todo'
        domain += searchbar_filters[filterby]['domain']
        
        # Count and paginate
        Task = request.env['ptt.vendor.task'].sudo()
        count = Task.search_count(domain)
        pager_values = portal_pager(
            url="/my/vendor-tasks",
            url_args={'filterby': filterby},
            total=count,
            page=page,
            step=20
        )
        
        tasks = Task.search(
            domain,
            limit=20,
            offset=pager_values['offset'],
            order='due_date asc, priority desc, sequence asc',
        )
        
        values.update({
            'tasks': tasks,
            'pager': pager_values,
            'searchbar_filters': searchbar_filters,
            'filterby': filterby,
            'page_name': 'vendor_tasks',
        })
        
        return request.render("ptt_vendor_management.portal_vendor_tasks", values)
    
    @http.route(['/my/vendor-task/<int:task_id>/update'], type='http', 
                auth="user", website=True, methods=['POST'], csrf=True)
    def portal_update_vendor_task(self, task_id, **kw):
        """Update task status or notes from portal."""
        partner = request.env.user.partner_id
        
        task = request.env['ptt.vendor.task'].sudo().browse(task_id)
        
        # Verify this task belongs to this vendor
        if not task.exists() or task.vendor_id.id != partner.id:
            return request.redirect('/my/vendor-tasks')
        
        action = kw.get('action', '')
        
        if action == 'start':
            task.action_start()
        elif action == 'done':
            task.action_done()
        elif action == 'reopen':
            task.action_reopen()
        
        # Update notes if provided
        notes = kw.get('notes', '').strip()
        if notes:
            task.write({'vendor_notes': notes})
        
        # Redirect back to work order or tasks page
        if kw.get('redirect_to_wo'):
            return request.redirect(f'/my/work-orders/{task.assignment_id.id}/{task.assignment_id.access_token}')
        return request.redirect('/my/vendor-tasks')
    
    @http.route(['/my/work-orders/<int:assignment_id>/<string:access_token>'], 
                type='http', auth="public", website=True)
    def portal_work_order_detail(self, assignment_id, access_token, **kw):
        """Public work order detail page (from email link).
        
        SECURITY: Only exposes LIMITED project info - NO customer pricing,
        NO other vendors, NO profitability data.
        """
        assignment = request.env['ptt.project.vendor.assignment'].sudo().browse(assignment_id)
        
        # Verify access token
        if not assignment.exists() or assignment.access_token != access_token:
            return request.render("website.404")
        
        # SECURITY: Only expose limited project info
        project = assignment.project_id
        
        # Get service type display name
        service_type_label = dict(assignment._fields['service_type'].selection).get(
            assignment.service_type, assignment.service_type
        )
        
        values = {
            'assignment': assignment,
            'token': access_token,
            # Event info for vendor - venue details needed for arrival
            'event_name': project.name,
            'event_date': project.ptt_event_date,
            'event_time_start': project.ptt_event_start_time or '',
            'event_time_end': project.ptt_event_end_time or '',
            'venue_name': project.ptt_venue_name or '',
            'venue_address': project.ptt_venue_address or '',
            # VENDOR'S assignment only - NO customer pricing, NO other vendors
            'service_type': service_type_label,
            'vendor_payment': assignment.actual_cost,
            'arrival_time': assignment.ptt_arrival_time or '',
            'special_instructions': assignment.notes or '',
            # Tasks for this assignment
            'vendor_tasks': assignment.vendor_task_ids,
            # Messages for communication (chatter)
            'messages': assignment.message_ids.filtered(
                lambda m: m.message_type in ('comment', 'notification')
            ),
        }
        
        return request.render("ptt_vendor_management.portal_work_order_detail", values)
    
    @http.route(['/my/work-orders/<int:assignment_id>/accept'], 
                type='json', auth="public", methods=['POST'])
    def portal_work_order_accept(self, assignment_id, access_token, signature=None, **kw):
        """Vendor accepts work order via JSON endpoint."""
        assignment = request.env['ptt.project.vendor.assignment'].sudo().browse(assignment_id)
        
        if not assignment.exists() or assignment.access_token != access_token:
            return {'success': False, 'error': 'Invalid token'}
        
        try:
            assignment.action_vendor_accept(signature=signature)
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @http.route(['/my/work-orders/<int:assignment_id>/decline'], 
                type='json', auth="public", methods=['POST'])
    def portal_work_order_decline(self, assignment_id, access_token, reason=None, **kw):
        """Vendor declines work order via JSON endpoint."""
        assignment = request.env['ptt.project.vendor.assignment'].sudo().browse(assignment_id)
        
        if not assignment.exists() or assignment.access_token != access_token:
            return {'success': False, 'error': 'Invalid token'}
        
        try:
            assignment.action_vendor_decline(reason=reason)
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @http.route(['/my/work-orders/<int:assignment_id>/message'], 
                type='http', auth="public", website=True, methods=['POST'], csrf=True)
    def portal_work_order_post_message(self, assignment_id, **kw):
        """Vendor posts a message on the work order.
        
        Posts message and notifies all followers (internal team) via email.
        """
        access_token = kw.get('access_token', '')
        assignment = request.env['ptt.project.vendor.assignment'].sudo().browse(assignment_id)
        
        if not assignment.exists() or assignment.access_token != access_token:
            return request.redirect('/my')
        
        message_body = kw.get('message', '').strip()
        
        if message_body:
            # Get internal team partners to notify (all followers except the vendor)
            internal_partners = assignment.message_partner_ids.filtered(
                lambda p: p.id != assignment.vendor_id.id
            )
            
            # Post message from vendor - notifies followers automatically with mt_comment
            assignment.message_post(
                body=f"<strong>Message from {assignment.vendor_id.name}:</strong><br/>{message_body}",
                message_type='comment',
                subtype_xmlid='mail.mt_comment',
                author_id=assignment.vendor_id.id,
                partner_ids=internal_partners.ids,  # Explicitly notify internal team
            )
        
        return request.redirect(f'/my/work-orders/{assignment_id}/{access_token}')
    
    # ==================== VENDOR APPLICATION ROUTES ====================
    
    @http.route(['/vendor/apply'], type='http', auth="user", website=True, csrf=True)
    def portal_vendor_application(self, **kw):
        """Vendor application form page."""
        values = self._prepare_portal_layout_values()
        
        partner = request.env.user.partner_id
        
        # Check if already a vendor
        if partner.supplier_rank > 0 and partner.ptt_vendor_status == 'active':
            return request.redirect('/my/applications')
        
        # Handle POST submission
        if request.httprequest.method == 'POST':
            return self._handle_vendor_application_submit(values, **kw)
        
        # Get services for the form
        services = request.env['ptt.vendor.service.type'].sudo().search([
            ('active', '=', True)
        ], order='name')
        
        # Get document types
        document_types = request.env['ptt.document.type'].sudo().search([
            ('active', '=', True)
        ], order='sequence, name')
        
        # Get US states
        us_country = request.env['res.country'].sudo().search([('code', '=', 'US')], limit=1)
        states = request.env['res.country.state'].sudo().search([
            ('country_id', '=', us_country.id)
        ], order='name') if us_country else []
        
        values.update({
            'partner': partner,
            'services': services,
            'document_types': document_types,
            'states': states,
            'kw': kw,
            'page_name': 'vendor_application',
        })
        
        return request.render("ptt_vendor_management.portal_vendor_application", values)
    
    def _handle_vendor_application_submit(self, values, **kw):
        """Process vendor application form submission."""
        try:
            # Validate required fields
            required_fields = [
                ('name', 'Company Name'),
                ('email', 'Company Email'),
                ('phone', 'Company Phone'),
                ('street', 'Street Address'),
                ('city', 'City'),
                ('state_id', 'State'),
                ('zip', 'ZIP Code'),
            ]
            
            missing = []
            for field, label in required_fields:
                if not kw.get(field, '').strip():
                    missing.append(label)
            
            if missing:
                raise ValueError(f"Required fields missing: {', '.join(missing)}")
            
            # Get service IDs
            service_ids = request.httprequest.form.getlist('service_ids[]')
            if not service_ids:
                raise ValueError("Please select at least one service.")
            
            service_ids = [int(s) for s in service_ids if str(s).isdigit()]
            
            # Create or update vendor partner
            partner = request.env.user.partner_id
            
            vendor_vals = {
                'name': kw.get('name', '').strip(),
                'email': kw.get('email', '').strip(),
                'phone': kw.get('phone', '').strip(),
                'street': kw.get('street', '').strip(),
                'street2': kw.get('street2', '').strip() or False,
                'city': kw.get('city', '').strip(),
                'state_id': int(kw.get('state_id')) if kw.get('state_id') else False,
                'zip': kw.get('zip', '').strip(),
                'website': kw.get('website_url', '').strip() or False,
                'is_company': True,
                'supplier_rank': 1,
                'ptt_vendor_status': 'pending_review',
                'ptt_vendor_principal_name': kw.get('principal_name', '').strip() or False,
                'ptt_vendor_additional_phone': kw.get('additional_phone', '').strip() or False,
                'ptt_vendor_zip_radius': float(kw.get('zip_radius', 0)) if kw.get('zip_radius') else 50.0,
                'ptt_vendor_notes': kw.get('vendor_notes', '').strip() or False,
                'ptt_portal_user_id': request.env.user.id,
                'ptt_vendor_service_types': [(6, 0, service_ids)],
            }
            
            # Check if we should update the current partner or create a new one
            if partner.is_company or not partner.parent_id:
                partner.sudo().write(vendor_vals)
                vendor = partner
            else:
                # Create a new company record
                vendor = request.env['res.partner'].sudo().create(vendor_vals)
            
            # Process document uploads
            self._process_document_uploads(vendor, kw)
            
            # Log note
            vendor.sudo().message_post(
                body=_("Vendor application submitted via portal by %s") % request.env.user.name,
                message_type="notification",
            )
            
            _logger.info("Vendor application submitted: %s (ID: %s)", vendor.name, vendor.id)
            
            # Return success
            values.update({
                'success': True,
                'vendor': vendor,
            })
            
        except ValueError as e:
            _logger.warning("Vendor application validation error: %s", str(e))
            values['error'] = str(e)
            values['kw'] = kw
            return self._render_application_form_with_error(values)
        except Exception as e:
            _logger.error("Vendor application error: %s", str(e))
            values['error'] = _("An error occurred. Please try again or contact support.")
            values['kw'] = kw
            return self._render_application_form_with_error(values)
        
        return request.render("ptt_vendor_management.portal_vendor_application", values)
    
    def _render_application_form_with_error(self, values):
        """Re-render application form with error and preserved data."""
        services = request.env['ptt.vendor.service.type'].sudo().search([
            ('active', '=', True)
        ], order='name')
        
        document_types = request.env['ptt.document.type'].sudo().search([
            ('active', '=', True)
        ], order='sequence, name')
        
        us_country = request.env['res.country'].sudo().search([('code', '=', 'US')], limit=1)
        states = request.env['res.country.state'].sudo().search([
            ('country_id', '=', us_country.id)
        ], order='name') if us_country else []
        
        values.update({
            'partner': request.env.user.partner_id,
            'services': services,
            'document_types': document_types,
            'states': states,
        })
        
        return request.render("ptt_vendor_management.portal_vendor_application", values)
    
    def _process_document_uploads(self, vendor, kw):
        """Process uploaded documents from the application form."""
        document_types = request.env['ptt.document.type'].sudo().search([('active', '=', True)])
        
        for doc_type in document_types:
            field_name = f"doc_{doc_type.id}"
            uploaded_file = request.httprequest.files.get(field_name)
            
            if uploaded_file and uploaded_file.filename:
                try:
                    file_content = uploaded_file.read()
                    file_b64 = base64.b64encode(file_content)
                    
                    # Get validity date if provided
                    validity_field = f"doc_{doc_type.id}_validity"
                    validity = False
                    if kw.get(validity_field):
                        try:
                            validity = fields.Date.from_string(kw.get(validity_field))
                        except Exception:
                            pass
                    
                    # Create document record
                    doc_vals = {
                        'vendor_id': vendor.id,
                        'document_type_id': doc_type.id,
                        'attached_document': file_b64,
                        'document_filename': uploaded_file.filename,
                        'status': 'non_compliant',
                        'validity': validity,
                    }
                    
                    request.env['ptt.vendor.document'].sudo().create(doc_vals)
                    _logger.info("Document uploaded for vendor %s: %s", vendor.id, doc_type.name)
                    
                except Exception as e:
                    _logger.error("Error uploading document %s: %s", doc_type.name, str(e))
    
    @http.route(['/my/applications'], type='http', auth="user", website=True)
    def portal_my_applications(self, **kw):
        """List user's vendor applications."""
        values = self._prepare_portal_layout_values()
        
        # Find vendor applications for this user
        domain = [
            '|',
            ('ptt_portal_user_id', '=', request.env.user.id),
            ('create_uid', '=', request.env.user.id),
            ('supplier_rank', '>', 0),
        ]
        
        applications = request.env['res.partner'].sudo().search(domain, order='create_date desc')
        
        values.update({
            'applications': applications,
            'page_name': 'vendor_applications',
        })
        
        return request.render("ptt_vendor_management.portal_my_vendor_applications", values)
    
    @http.route(['/my/application/<int:application_id>'], type='http', auth="user", website=True)
    def portal_application_detail(self, application_id, **kw):
        """Show vendor application detail page."""
        values = self._prepare_portal_layout_values()
        
        vendor = request.env['res.partner'].sudo().browse(application_id)
        
        # Security check
        if not vendor.exists() or (
            vendor.ptt_portal_user_id.id != request.env.user.id and 
            vendor.create_uid.id != request.env.user.id
        ):
            return request.redirect('/my/applications')
        
        values.update({
            'vendor': vendor,
            'page_name': 'application_detail',
        })
        
        return request.render("ptt_vendor_management.portal_vendor_application_detail", values)
    
    @http.route(['/my/application/<int:application_id>/document/<int:document_id>/download'], 
                type='http', auth="user", website=True)
    def portal_document_download(self, application_id, document_id, **kw):
        """Download a vendor document."""
        vendor = request.env['res.partner'].sudo().browse(application_id)
        
        # Security check
        if not vendor.exists() or (
            vendor.ptt_portal_user_id.id != request.env.user.id and 
            vendor.create_uid.id != request.env.user.id
        ):
            return request.redirect('/my/applications')
        
        document = request.env['ptt.vendor.document'].sudo().browse(document_id)
        
        # Verify document belongs to this vendor
        if document.vendor_id.id != vendor.id:
            return request.redirect(f'/my/application/{application_id}')
        
        if not document.attached_document:
            return request.redirect(f'/my/application/{application_id}')
        
        filename = document.document_filename or f"document_{document_id}"
        
        return request.make_response(
            base64.b64decode(document.attached_document),
            headers=[
                ('Content-Type', 'application/octet-stream'),
                ('Content-Disposition', f'attachment; filename="{filename}"'),
            ]
        )
    
    # ==================== VENDOR RFQ PORTAL ROUTES ====================
    
    @http.route(['/my/vendor_rfqs', '/my/vendor_rfqs/page/<int:page>'], 
                type='http', auth="user", website=True)
    def portal_my_vendor_rfqs(self, page=1, sortby=None, filterby=None, **kw):
        """Display RFQs the vendor is invited to."""
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        
        domain = [
            ('vendor_ids', 'in', partner.ids),
            ('state', 'not in', ['draft']),
        ]
        
        # Sorting
        searchbar_sortings = {
            'date': {'label': _('Newest'), 'order': 'create_date desc'},
            'name': {'label': _('Reference'), 'order': 'name asc'},
            'closing': {'label': _('Closing Date'), 'order': 'closing_date asc'},
        }
        
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']
        
        # Filtering
        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
            'open': {'label': _('Open'), 'domain': [('state', '=', 'in_progress')]},
            'closed': {'label': _('Closed'), 'domain': [('state', 'in', ['done', 'order'])]},
        }
        
        if not filterby:
            filterby = 'all'
        domain += searchbar_filters[filterby]['domain']
        
        # Count and paginate
        RFQ = request.env['ptt.vendor.rfq'].sudo()
        count = RFQ.search_count(domain)
        
        pager_values = portal_pager(
            url="/my/vendor_rfqs",
            url_args={'sortby': sortby, 'filterby': filterby},
            total=count,
            page=page,
            step=10
        )
        
        rfqs = RFQ.search(
            domain,
            order=order,
            limit=10,
            offset=pager_values['offset']
        )
        
        values.update({
            'rfqs': rfqs,
            'pager': pager_values,
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'searchbar_filters': searchbar_filters,
            'filterby': filterby,
            'page_name': 'vendor_rfq',
        })
        
        return request.render("ptt_vendor_management.portal_my_vendor_rfqs", values)
    
    @http.route(['/my/vendor_rfq/<int:rfq_id>'], type='http', auth="user", website=True)
    def portal_vendor_rfq_detail(self, rfq_id, **kw):
        """Display RFQ detail page where vendor can submit quote."""
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        
        rfq = request.env['ptt.vendor.rfq'].sudo().browse(rfq_id)
        
        # Verify vendor is invited to this RFQ
        if not rfq.exists() or partner not in rfq.vendor_ids:
            return request.redirect('/my/vendor_rfqs')
        
        # Get vendor's existing quote if any
        my_quote = rfq.quote_history_ids.filtered(
            lambda q: q.vendor_id == partner
        )
        my_quote = my_quote[0] if my_quote else False
        
        values.update({
            'vendor_rfq': rfq,
            'my_quote': my_quote,
            'partner': partner,
            'page_name': 'vendor_rfq',
        })
        
        return request.render("ptt_vendor_management.portal_vendor_rfq_detail", values)
    
    @http.route(['/vendor_rfq/submit_quote'], type='http', auth="user", 
                website=True, methods=['POST'], csrf=True)
    def portal_submit_rfq_quote(self, **kw):
        """Submit or update vendor quote for an RFQ."""
        rfq_id = int(kw.get('rfq_id', 0))
        partner = request.env.user.partner_id
        
        rfq = request.env['ptt.vendor.rfq'].sudo().browse(rfq_id)
        
        # Verify vendor is invited and RFQ is open
        if not rfq.exists() or partner not in rfq.vendor_ids:
            return request.redirect('/my/vendor_rfqs')
        
        if rfq.state != 'in_progress':
            return request.redirect(f'/my/vendor_rfq/{rfq_id}')
        
        # Parse quote data
        try:
            price = float(kw.get('price', 0))
        except (ValueError, TypeError):
            price = 0.0
        
        delivery_date = kw.get('delivery_date') or False
        note = kw.get('note', '').strip() or False
        
        # Check if vendor already has a quote
        existing_quote = rfq.quote_history_ids.filtered(
            lambda q: q.vendor_id == partner
        )
        
        if existing_quote:
            # Update existing quote
            existing_quote[0].write({
                'quoted_price': price,
                'estimate_date': delivery_date,
                'note': note,
                'submit_date': fields.Datetime.now(),
            })
        else:
            # Create new quote
            request.env['ptt.vendor.quote.history'].sudo().create({
                'rfq_id': rfq.id,
                'vendor_id': partner.id,
                'quoted_price': price,
                'estimate_date': delivery_date,
                'note': note,
                'currency_id': rfq.currency_id.id,
            })
        
        return request.redirect(f'/my/vendor_rfq/{rfq_id}')

