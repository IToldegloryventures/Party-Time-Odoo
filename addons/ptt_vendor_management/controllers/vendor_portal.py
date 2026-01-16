"""
Vendor Portal Controller - Work Order Access

Reference: https://www.odoo.com/documentation/19.0/developer/reference/backend/http.html
"""
from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager


class VendorPortal(CustomerPortal):
    """Extend portal for vendor work order access."""
    
    def _prepare_home_portal_values(self, counters):
        """Add work order count to portal home."""
        values = super()._prepare_home_portal_values(counters)
        
        partner = request.env.user.partner_id
        Assignment = request.env['ptt.project.vendor.assignment']
        
        if 'work_order_count' in counters:
            domain = [('vendor_id', '=', partner.id)]
            try:
                count = Assignment.search_count(domain) \
                    if Assignment.check_access_rights('read', raise_exception=False) else 0
            except Exception:
                count = 0
            values['work_order_count'] = count
        
        return values
    
    @http.route(['/my/work-orders', '/my/work-orders/page/<int:page>'], 
                type='http', auth="user", website=True)
    def portal_my_work_orders(self, page=1, sortby=None, filterby=None, **kw):
        """Display vendor's work orders list."""
        values = self._prepare_portal_layout_values()
        Assignment = request.env['ptt.project.vendor.assignment']
        partner = request.env.user.partner_id
        
        domain = [('vendor_id', '=', partner.id)]
        
        # Filters
        searchbar_filters = {
            'all': {'label': 'All', 'domain': []},
            'pending': {'label': 'Pending', 'domain': [('state', '=', 'sent')]},
            'accepted': {'label': 'Accepted', 'domain': [('state', '=', 'accepted')]},
        }
        
        if not filterby:
            filterby = 'all'
        domain += searchbar_filters[filterby]['domain']
        
        # Count and paginate
        count = Assignment.search_count(domain)
        pager_values = portal_pager(
            url="/my/work-orders",
            total=count,
            page=page,
            step=10
        )
        
        assignments = Assignment.search(
            domain, 
            limit=10, 
            offset=pager_values['offset'],
            order='create_date desc'
        )
        
        values.update({
            'assignments': assignments,
            'pager': pager_values,
            'searchbar_filters': searchbar_filters,
            'filterby': filterby,
            'page_name': 'work_orders',
        })
        
        return request.render("ptt_vendor_management.portal_my_work_orders", values)
    
    @http.route(['/my/work-orders/<int:assignment_id>/<string:access_token>'], 
                type='http', auth="public", website=True)
    def portal_work_order_detail(self, assignment_id, access_token, **kw):
        """Public work order detail page (from email link).
        
        SECURITY: Only exposes LIMITED project info - NO customer pricing,
        NO other vendors, NO profitability data.
        """
        assignment = request.env['ptt.project.vendor.assignment'].sudo().browse(assignment_id)
        
        # Verify access token (includes expiry check if available)
        if not assignment.exists():
            return request.render("website.404")
        
        # Use enhanced token validation if available
        if hasattr(assignment, '_is_token_valid'):
            if not assignment._is_token_valid(access_token):
                return request.render("website.404")
        elif assignment.access_token != access_token:
            return request.render("website.404")
        
        # SECURITY: Only expose limited project info
        project = assignment.project_id
        
        # Defensive check: ensure project exists before accessing its fields
        if not project:
            return request.render("website.404")
        
        # Get service type display name (defensive - selection may not exist)
        service_type_label = assignment.service_type or ''
        if 'service_type' in assignment._fields and hasattr(assignment._fields['service_type'], 'selection'):
            selection = assignment._fields['service_type'].selection
            if callable(selection):
                try:
                    selection = selection(assignment)
                except Exception:
                    selection = []
            service_type_label = dict(selection).get(assignment.service_type, assignment.service_type) or ''
        
        values = {
            'assignment': assignment,
            'token': access_token,
            # LIMITED event info - NO financials, NO other vendors
            'event_name': project.name or 'TBD',
            'event_date': project.ptt_event_date if hasattr(project, 'ptt_event_date') else False,
            'event_time_start': getattr(project, 'ptt_event_start_time', '') or '',
            'event_time_end': getattr(project, 'ptt_event_end_time', '') or '',
            'venue_name': getattr(project, 'ptt_venue_name', '') or '',
            'venue_address': '',  # Only add if ptt_venue_address field exists
            # VENDOR'S assignment only
            'service_type': service_type_label,
            'vendor_payment': assignment.actual_cost if hasattr(assignment, 'actual_cost') else 0.0,
            'arrival_time': getattr(assignment, 'ptt_arrival_time', '') or '',
            'special_instructions': assignment.notes or '' if hasattr(assignment, 'notes') else '',
        }
        
        return request.render("ptt_vendor_management.portal_work_order_detail", values)
    
    @http.route(['/my/work-orders/<int:assignment_id>/accept'], 
                type='jsonrpc', auth="public", methods=['POST'])
    def portal_work_order_accept(self, assignment_id, access_token, signature=None, **kw):
        """Vendor accepts work order via JSON endpoint."""
        assignment = request.env['ptt.project.vendor.assignment'].sudo().browse(assignment_id)
        
        if not assignment.exists():
            return {'success': False, 'error': 'Invalid token'}
        
        # Use enhanced token validation if available
        if hasattr(assignment, '_is_token_valid'):
            if not assignment._is_token_valid(access_token):
                return {'success': False, 'error': 'Token expired or invalid'}
        elif assignment.access_token != access_token:
            return {'success': False, 'error': 'Invalid token'}
        
        try:
            assignment.action_vendor_accept(signature=signature)
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @http.route(['/my/work-orders/<int:assignment_id>/decline'], 
                type='jsonrpc', auth="public", methods=['POST'])
    def portal_work_order_decline(self, assignment_id, access_token, reason=None, **kw):
        """Vendor declines work order via JSON endpoint."""
        assignment = request.env['ptt.project.vendor.assignment'].sudo().browse(assignment_id)
        
        if not assignment.exists():
            return {'success': False, 'error': 'Invalid token'}
        
        # Use enhanced token validation if available
        if hasattr(assignment, '_is_token_valid'):
            if not assignment._is_token_valid(access_token):
                return {'success': False, 'error': 'Token expired or invalid'}
        elif assignment.access_token != access_token:
            return {'success': False, 'error': 'Invalid token'}
        
        try:
            assignment.action_vendor_decline(reason=reason)
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
