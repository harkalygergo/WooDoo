from odoo import http

class HelloWorld(http.Controller):
    # This route makes the 'hello' method accessible at '/hello'
    @http.route('/hello', auth='public', website=True)
    def hello(self, **kw):
        # The 'woo_connector.hello_page' is the ID of the template defined in XML.
        # This now correctly references the template within the new module name.
        return http.request.render('woo_connector.hello_world_templates', {})

    # You can also return a simple string without a template
    @http.route('/hello/string', auth='public')
    def hello_string(self, **kw):
        return "Hello World! (from a simple string)"
