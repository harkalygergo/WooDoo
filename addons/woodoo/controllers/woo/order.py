import json
from odoo import http, api
from addons.woodoo.controllers.woo.api import WooAPI


class Orders(http.Controller):
    @http.route('/woodoo/woo/orders/show', auth='public')
    def show(self):
        return http.Response(
            json.dumps(self.get()),
            content_type='application/json; charset=utf-8'
        )

    def get(self):
        try:
            wooAPI = WooAPI.get(self)
            response = wooAPI.get("orders", params={"per_page": 5})
            if response.status_code != 200:
                return print("API error:", response.status_code, response.text)
            else:
                return response.json()
        except Exception as e:
            print("Error:", e)

    # from addons.woodoo.controllers.woo.order import Orders
    # Orders.create(self, created_date, 'WC-gergo-8755')
    def create(self, createdAt, name):
        try:
            env = api.Environment(http.request.cr, http.request.uid, {})
            #order_time = datetime.now()
            #order_name = f"WOODOOgergo-{order_time.strftime('%Y%m%d%H%M%S')}"
            partner = env['res.partner'].search([], limit=1)
            product = env['product.product'].search([], limit=1)
            order_line = [(0, 0, {
                'product_id': product.id,
                'product_uom_qty': 1,
            })]
            order = env['sale.order'].create({
                'name': name,
                #'created_date': createdAt,
                'partner_id': partner.id,
                'order_line': order_line,
            })
            return print(f"Created Sale Order: {order.name}")
        except Exception as e:
            print("Error:", e)
