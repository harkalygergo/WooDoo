from odoo import http
import subprocess
import sys
import os

class HelloWorld(http.Controller):
    # This route makes the 'hello' method accessible at '/hello'
    @http.route('/hello', type='http', auth='public', website=True)
    def hello(self, **kw):
        return http.request.render('woodoo.hello_world_template')

    # You can also return a simple string without a template
    @http.route('/hello/string', auth='public')
    def hello_string(self, **kw):
        return "Hello from WooDoo!"

    @http.route('/woodoo/wp-orders', auth='public')
    def wp_orders(self, **kw):
        script_path = os.path.join(os.path.dirname(__file__), '../scripts/get-woocommerce-orders.py')
        result = subprocess.run([sys.executable, script_path], capture_output=True, text=True)
        if result.returncode != 0:
            return f"Error executing script: {result.stderr}"
        return f"Script output:<br><pre>{result.stdout}</pre>"
