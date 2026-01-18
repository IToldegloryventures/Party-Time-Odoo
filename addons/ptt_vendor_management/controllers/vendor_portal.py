# Part of Party Time Texas Event Management System
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
"""
Vendor Portal Controllers.

Handles the web routes for vendor portal access.
"""

from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal


class VendorPortal(CustomerPortal):
    """Vendor Portal Controller."""
    
    @http.route(['/my/vendor/assignments', '/my/vendor/assignments/page/<int:page>'],
                type='http', auth='user', website=True)
    def portal_vendor_assignments(self, page=1, sortby=None, **kw):
        """List vendor assignments for the logged-in vendor."""
        partner = request.env.user.partner_id
        
        if not partner.ptt_is_vendor:
            return request.redirect('/my')
        
        Assignment = request.env['ptt.project.vendor.assignment']
        
        domain = [
            ('vendor_id', '=', partner.id),
            ('status', 'not in', ['cancelled']),
        ]
        
        # Sorting options
        searchbar_sortings = {
            'date': {'label': _('Service Date'), 'order': 'service_date desc'},
            'project': {'label': _('Project'), 'order': 'project_id'},
            'status': {'label': _('Status'), 'order': 'status'},
        }
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']
        
        # Count for pager
        assignment_count = Assignment.search_count(domain)
        
        # Pager
        pager = request.website.pager(
            url="/my/vendor/assignments",
            total=assignment_count,
            page=page,
            step=10,
        )
        
        # Get assignments
        assignments = Assignment.search(
            domain, 
            order=order, 
            limit=10, 
            offset=pager['offset']
        )
        
        values = {
            'assignments': assignments,
            'page_name': 'vendor_assignments',
            'pager': pager,
            'default_url': '/my/vendor/assignments',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        }
        
        return request.render(
            'ptt_vendor_management.portal_vendor_assignments',
            values
        )
    
    @http.route(['/my/vendor/assignment/<int:assignment_id>'],
                type='http', auth='user', website=True)
    def portal_vendor_assignment_detail(self, assignment_id, access_token=None, **kw):
        """View details of a specific vendor assignment."""
        partner = request.env.user.partner_id
        
        Assignment = request.env['ptt.project.vendor.assignment']
        assignment = Assignment.browse(assignment_id)
        
        # Security check
        if not assignment.exists():
            return request.redirect('/my/vendor/assignments')
        
        # Allow access if vendor matches or has valid (non-expired) token
        if assignment.vendor_id.id != partner.id:
            if not assignment._is_token_valid(access_token):
                return request.redirect('/my/vendor/assignments')
        
        values = {
            'assignment': assignment,
            'page_name': 'vendor_assignment_detail',
        }
        
        return request.render(
            'ptt_vendor_management.portal_vendor_assignment_detail',
            values
        )
    
    @http.route(['/my/vendor/assignment/<int:assignment_id>/confirm'],
                type='http', auth='user', website=True, methods=['POST'])
    def portal_vendor_assignment_confirm(self, assignment_id, **kw):
        """Confirm a vendor assignment from the portal."""
        partner = request.env.user.partner_id
        
        Assignment = request.env['ptt.project.vendor.assignment']
        assignment = Assignment.browse(assignment_id)
        
        if assignment.exists() and assignment.vendor_id.id == partner.id:
            assignment.action_vendor_confirm()
        
        return request.redirect(f'/my/vendor/assignment/{assignment_id}')
    
    @http.route(['/my/vendor/assignment/<int:assignment_id>/decline'],
                type='http', auth='user', website=True, methods=['POST'])
    def portal_vendor_assignment_decline(self, assignment_id, **kw):
        """Decline a vendor assignment from the portal."""
        partner = request.env.user.partner_id
        
        Assignment = request.env['ptt.project.vendor.assignment']
        assignment = Assignment.browse(assignment_id)
        
        if assignment.exists() and assignment.vendor_id.id == partner.id:
            assignment.action_vendor_decline()
        
        return request.redirect('/my/vendor/assignments')

    # =========================================
    # RFQ Portal Routes
    # =========================================
    
    def _prepare_home_portal_values(self, counters):
        """Add vendor counts to portal home (override to include RFQ)."""
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id
        
        if 'vendor_assignment_count' in counters:
            if partner.ptt_is_vendor:
                assignment_count = request.env['ptt.project.vendor.assignment'].search_count([
                    ('vendor_id', '=', partner.id),
                    ('status', 'not in', ['cancelled']),
                ])
                values['vendor_assignment_count'] = assignment_count
            else:
                values['vendor_assignment_count'] = 0
        
        if 'rfq_count' in counters:
            if partner.ptt_is_vendor:
                rfq_count = request.env['ptt.vendor.rfq'].search_count([
                    ('vendor_ids', 'in', [partner.id]),
                    ('state', 'in', ['sent', 'in_progress']),
                ])
                values['rfq_count'] = rfq_count
            else:
                values['rfq_count'] = 0
        
        return values
    
    @http.route(['/my/vendor/rfq', '/my/vendor/rfq/page/<int:page>'],
                type='http', auth='user', website=True)
    def portal_vendor_rfq_list(self, page=1, sortby=None, filterby=None, **kw):
        """List RFQs for the logged-in vendor."""
        partner = request.env.user.partner_id
        
        if not partner.ptt_is_vendor:
            return request.redirect('/my')
        
        RFQ = request.env['ptt.vendor.rfq']
        
        # Base domain - RFQs sent to this vendor
        domain = [('vendor_ids', 'in', [partner.id])]
        
        # Filter options
        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
            'open': {'label': _('Open'), 'domain': [('state', 'in', ['sent', 'in_progress'])]},
            'closed': {'label': _('Closed'), 'domain': [('state', 'in', ['done', 'assigned'])]},
        }
        if not filterby:
            filterby = 'open'
        domain += searchbar_filters[filterby]['domain']
        
        # Sorting options
        searchbar_sortings = {
            'closing_date': {'label': _('Deadline'), 'order': 'closing_date asc'},
            'date': {'label': _('Event Date'), 'order': 'event_date desc'},
            'name': {'label': _('Reference'), 'order': 'name'},
        }
        if not sortby:
            sortby = 'closing_date'
        order = searchbar_sortings[sortby]['order']
        
        # Count for pager
        rfq_count = RFQ.search_count(domain)
        
        # Pager
        pager = request.website.pager(
            url="/my/vendor/rfq",
            total=rfq_count,
            page=page,
            step=10,
            url_args={'sortby': sortby, 'filterby': filterby},
        )
        
        # Get RFQs
        rfqs = RFQ.search(domain, order=order, limit=10, offset=pager['offset'])
        
        values = {
            'rfqs': rfqs,
            'page_name': 'vendor_rfq',
            'pager': pager,
            'default_url': '/my/vendor/rfq',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'searchbar_filters': searchbar_filters,
            'filterby': filterby,
        }
        
        return request.render('ptt_vendor_management.portal_vendor_rfq_list', values)
    
    @http.route(['/my/vendor/rfq/<int:rfq_id>'],
                type='http', auth='user', website=True)
    def portal_vendor_rfq_detail(self, rfq_id, **kw):
        """View details of a specific RFQ."""
        partner = request.env.user.partner_id
        
        RFQ = request.env['ptt.vendor.rfq']
        rfq = RFQ.browse(rfq_id)
        
        # Security check
        if not rfq.exists():
            return request.redirect('/my/vendor/rfq')
        
        # Check vendor is invited to this RFQ
        if partner.id not in rfq.vendor_ids.ids:
            return request.redirect('/my/vendor/rfq')
        
        values = {
            'rfq': rfq,
            'page_name': 'vendor_rfq_detail',
        }
        
        return request.render('ptt_vendor_management.portal_vendor_rfq_detail', values)
    
    @http.route(['/my/vendor/rfq/<int:rfq_id>/submit'],
                type='http', auth='user', website=True, methods=['POST'])
    def portal_vendor_rfq_submit_quote(self, rfq_id, **kw):
        """Submit or update a quote for an RFQ."""
        partner = request.env.user.partner_id
        
        RFQ = request.env['ptt.vendor.rfq']
        rfq = RFQ.browse(rfq_id)
        
        # Security check
        if not rfq.exists() or partner.id not in rfq.vendor_ids.ids:
            return request.redirect('/my/vendor/rfq')
        
        # Check RFQ is still open
        if rfq.state not in ('sent', 'in_progress'):
            return request.redirect(f'/my/vendor/rfq/{rfq_id}')
        
        # Get quote data
        quoted_price = float(kw.get('quoted_amount', 0))
        notes = kw.get('notes', '')
        
        if quoted_price <= 0:
            return request.redirect(f'/my/vendor/rfq/{rfq_id}')
        
        # Find existing quote or create new
        QuoteHistory = request.env['ptt.vendor.quote.history']
        existing_quote = QuoteHistory.search([
            ('rfq_id', '=', rfq.id),
            ('vendor_id', '=', partner.id),
        ], limit=1)
        
        from datetime import datetime
        
        if existing_quote:
            existing_quote.write({
                'quoted_price': quoted_price,
                'notes': notes,
                'quote_date': datetime.now(),
            })
        else:
            QuoteHistory.create({
                'rfq_id': rfq.id,
                'vendor_id': partner.id,
                'quoted_price': quoted_price,
                'notes': notes,
            })
        
        # Update RFQ state if still in 'sent'
        if rfq.state == 'sent':
            rfq.write({'state': 'in_progress'})
        
        return request.redirect(f'/my/vendor/rfq/{rfq_id}')
