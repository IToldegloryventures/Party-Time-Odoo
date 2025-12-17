from odoo import http
from odoo.http import request


class AwesomeOwlController(http.Controller):
    """Simple controller to serve the Owl playground page.

    Route: /awesome_owl
    """

    @http.route("/awesome_owl", type="http", auth="user", website=True)
    def awesome_owl_playground(self, **kwargs):
        return request.render("awesome_owl.playground_page", {})


