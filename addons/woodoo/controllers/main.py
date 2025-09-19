from odoo import http, api, fields


class HelloWorld(http.Controller):
    # You can also return a simple string without a template
    @http.route('/hello/string', auth='public')
    def hello_string(self, **kw):
        return "Hello from WooDoo!"
