from datetime import datetime
from odoo import http, api, fields
from addons.woodoo.controllers.order import Order
from addons.woodoo.controllers.woo.order import Orders


class HelloWorld(http.Controller):
    # This route makes the 'hello' method accessible at '/hello'
    @http.route('/hello', type='http', auth='public', website=True)
    def hello(self, **kw):
        return http.request.render('woodoo.hello_world_template')

    # You can also return a simple string without a template
    @http.route('/hello/string', auth='public')
    def hello_string(self, **kw):
        return "Hello from WooDoo!"

    @http.route('/api/create_order', auth='public')
    def create_order(self, **kw):
        # Odoo shell or script with environment loaded
        env = http.request.env

        # Find a partner and a product
        partner = env['res.partner'].search([], limit=1)
        product = env['product.product'].search([], limit=1)

        # Prepare order line
        order_line = [(0, 0, {
            'product_id': product.id,
            'product_uom_qty': 1,
        })]

        # Create sale order
        order = env['sale.order'].create({
            'partner_id': partner.id,
            'order_line': order_line,
        })

        print(f"Created Sale Order: {order.name}")

    @http.route('/woodoo/create_order', auth='public')
    def woodoo_create_order(self):
        # use woo directory orders.py get function

        # create date like: 2025-09-10 12:34:12.750476
        created_date = datetime.now()

        Order.create(self, created_date, 'WC-8755')
        """
        order_time = datetime.now()
        order_name = f"WOODOO-{order_time.strftime('%Y%m%d%H%M%S')}"
        env = api.Environment(http.request.cr, http.request.uid, {})
        partner = env['res.partner'].search([], limit=1)
        product = env['product.product'].search([], limit=1)
        order_line = [(0, 0, {
            'product_id': product.id,
            'product_uom_qty': 1,
        })]
        order = env['sale.order'].create({
            'name': order_name,
            'partner_id': partner.id,
            'order_line': order_line,
        })
        return print(f"Created Sale Order: {order.name}")
        """

    def create_order_route(self, **kw):
        sample_order = {
            "id": 123,
            "number": "1001",
            "date_created": "2024-10-01T12:00:00",
            "total": "99.99",
        }
        order = self.woodoo_create_order(sample_order)
        return f"Created Order: {order.name}"
