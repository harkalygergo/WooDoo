from odoo import http, api, fields


class HelloWorld(http.Controller):
    # This route makes the 'hello' method accessible at '/hello'
    @http.route('/hello', type='http', auth='public', website=True)
    def hello(self, **kw):
        return http.request.render('woodoo.hello_world_template')

    # You can also return a simple string without a template
    @http.route('/hello/string', auth='public')
    def hello_string(self, **kw):
        return "Hello from WooDoo!"
