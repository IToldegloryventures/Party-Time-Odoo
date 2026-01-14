# -*- coding: utf-8 -*-

from odoo import http

# class ppt_event_management(http.Controller):
#     @http.route('/ppt_event_management/ppt_event_management/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('ppt_event_management.listing', {
#             'root': '/ppt_event_management/ppt_event_management',
#             'objects': http.request.env['ppt_event_management.ppt_event_management'].search([]),
#         })
#
#     @http.route('/ppt_event_management/ppt_event_management/objects/<model("ppt_event_management.ppt_event_management"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ppt_event_management.object', {
#             'object': obj
#         })
