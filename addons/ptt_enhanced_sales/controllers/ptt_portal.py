# -*- coding: utf-8 -*-
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import request, route
from odoo import http, _

class PTTSalePortal(CustomerPortal):
    @http.route(['/my/orders/<int:order_id>'], type='http', auth='public', website=True)
    def portal_my_sale_order(self, order_id=None, access_token=None, report_type=None, message=None, download=False, **kw):
        response = super().portal_my_sale_order(order_id=order_id, access_token=access_token, report_type=report_type, message=message, download=download, **kw)
        # The template override will handle the initials field display
        return response

    @http.route(['/my/orders/<int:order_id>/sign'], type='jsonrpc', auth='public', website=True)
    def portal_order_sign(self, order_id, access_token=None, signature=None, name=None, **post):
        order = request.env['sale.order'].sudo().browse(order_id)
        initials = post.get('ptt_client_initials') or request.params.get('ptt_client_initials')
        if not initials:
            return {'error': _('You must enter your initials to accept the Terms and Conditions.')}
        order.ptt_client_initials = initials
        return super().portal_order_sign(order_id, access_token=access_token, signature=signature, name=name, **post)
