# -*- coding: utf-8 -*-
"""
Vendor Intake Portal Controller - Public Vendor Application Form
Odoo 19.0 compliant
"""
from odoo import http
from odoo.http import request


class VendorIntakePortal(http.Controller):
    @http.route(
        ['/vendor/intake', '/vendor/intake/submit'],
        type='http', auth='public', website=True, csrf=True
    )
    def vendor_intake_form(self, **post):
        if request.httprequest.method == 'POST' and post:
            # Process form submission (simplified, expand as needed)
            vals = {
                'name': post.get('company_name') or post.get('name'),
                'email': post.get('email'),
                'phone': post.get('phone'),
                'supplier_rank': 1,
            }
            # Add vendor type if provided and field exists
            if post.get('vendor_type'):
                vals['ptt_vendor_type'] = post.get('vendor_type')
            # Add address if provided
            if post.get('address'):
                vals['street'] = post.get('address')
            
            partner = request.env['res.partner'].sudo().create(vals)
            return request.render(
                'ptt_vendor_management.vendor_intake_thankyou',
                {'partner': partner}
            )
        # Render the intake form
        return request.render('ptt_vendor_management.vendor_intake_form', {})
