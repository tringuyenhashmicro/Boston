# -*- coding: utf-8 -*-
from openerp import http

# class BostonModifierAccessRight(http.Controller):
#     @http.route('/boston_modifier_access_right/boston_modifier_access_right/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/boston_modifier_access_right/boston_modifier_access_right/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('boston_modifier_access_right.listing', {
#             'root': '/boston_modifier_access_right/boston_modifier_access_right',
#             'objects': http.request.env['boston_modifier_access_right.boston_modifier_access_right'].search([]),
#         })

#     @http.route('/boston_modifier_access_right/boston_modifier_access_right/objects/<model("boston_modifier_access_right.boston_modifier_access_right"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('boston_modifier_access_right.object', {
#             'object': obj
#         })