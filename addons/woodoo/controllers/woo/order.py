import json
from odoo import http, api
from addons.woodoo.controllers.woo.api import WooAPI


class Orders(http.Controller):
    @http.route('/woodoo/woo/orders/show', auth='public')
    def show(self):

        orders = self.get()
        self.sync(orders)

        return http.Response(
            json.dumps(orders),
            content_type='application/json; charset=utf-8'
        )

    def sync(self, orders):
        try:
            for order in orders:
                created_date = order.get('date_created')
                name = order.get('number')
                self.create(order, created_date, f"WC--{name}")
            return True
        except Exception as e:
            print("Error:", e)
            return False


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
    def create(self, order, createdAt, name):
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
                'currency_id': env['res.currency'].search([('name', '=', order.get("currency"))], limit=1).id,
                'state': self.switchOrderStatus(order.get("status", "draft")),
                # set odoo order total as order.get("total")
                'amount_total': float(order.get("total", 0.0)),
            })
            return print(f"Created Sale Order: {order.name}")
        except Exception as e:
            print("Error:", e)


    def switchOrderStatus(self, orderStatus):
        statusMapping = {
            'pending': 'draft',
            'processing': 'sale',
            'on-hold': 'sale',
            'completed': 'sale',
            'cancelled': 'cancel',
            'refunded': 'cancel',
            'failed': 'cancel',
        }
        return statusMapping.get(orderStatus, 'draft')
