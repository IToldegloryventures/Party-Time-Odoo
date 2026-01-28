# -*- coding: utf-8 -*-
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.http import request, route
from odoo import http, _

class PTTCustomerPortal(CustomerPortal):
    
    @route(['/my/orders/<int:order_id>/accept'], type='http', auth='public', website=True, csrf=True)
    def portal_order_accept(self, order_id=None, access_token=None, **post):
        order = request.env['sale.order'].sudo().browse(order_id)
        if not order or not order.exists():
            return request.not_found()
        initials = post.get('ptt_client_initials')
        if not initials:
            return request.render('ptt_enhanced_sales.portal_sale_order_client_initials', {
                'sale_order': order,
                'error': _('You must enter your initials to accept the Terms and Conditions.'),
            })
        order.ptt_client_initials = initials
        # Continue with standard confirmation logic (signature/payment/etc.)
        return super(PTTCustomerPortal, self).portal_order_accept(order_id=order_id, access_token=access_token, **post)
