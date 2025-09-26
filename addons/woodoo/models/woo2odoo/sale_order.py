import os
from datetime import date
from odoo import api, http, fields, models
from addons.woodoo.controllers.woo.api import WooAPI
from addons.woodoo.controllers.woo.partner import Partner
from addons.woodoo.controllers.woo.product import Product


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def cron(self, max_orders=20):
        try:
            orders = self.get(max_orders)
            self.sync(orders)
            return True
        except Exception as e:
            print("Error:", e)
            return False

    def get(self, max_orders=20):
        try:
            wooAPI = WooAPI.get(self)
            today = date.today().isoformat()
            response = wooAPI.get("orders", params={
                "per_page": max_orders,
                "after": f"{today}T00:00:00"
            })
            if response.status_code != 200:
                return print("API error:", response.status_code, response.text)
            else:
                orders = response.json()
                if isinstance(orders, list):
                    return orders
                else:
                    print("Unexpected response:", orders)
        except Exception as e:
            print("Error:", e)

    def sync(self, orders):
        try:
            for order in orders:
                self.create(order)
            return True
        except Exception as e:
            print("Error:", e)
            return False

    def create(self, order):
        try:
            env = api.Environment(http.request.cr, http.request.uid, {})
            orderName = f"WOO-{os.getenv('WP_URL')}-{order.get('id')}"
            # check if order already exists by name
            existingOrder = env['sale.order'].search([('name', '=', orderName)], limit=1)
            if existingOrder:
                return print("Order already exists:", existingOrder.name)

            # PARTNER
            orderBilling = order.get('billing')
            orderShipping = order.get('shipping')
            # find partner by billing email
            partner = Partner.find_by_email(self, orderBilling.get("email"))
            # if not found, create partner first
            partner = Partner.create(self, partner)

            # SHIPPING
            partnerShipping = partner
            # check if billing and shipping first_name, last_name, company, address_1, address_2, city, state, postcode, country, phone different
            if orderBilling.get("first_name") != orderShipping.get("first_name") or \
               orderBilling.get("last_name") != orderShipping.get("last_name") or \
               orderBilling.get("address_1") != orderShipping.get("address_1") or \
               orderBilling.get("address_2") != orderShipping.get("address_2") or \
               orderBilling.get("city") != orderShipping.get("city") or \
               orderBilling.get("state") != orderShipping.get("state") or \
               orderBilling.get("postcode") != orderShipping.get("postcode") or \
               orderBilling.get("country") != orderShipping.get("country") or \
               orderBilling.get("phone") != orderShipping.get("phone") or \
               orderBilling.get("company") != orderShipping.get("company"):
                # if different, create new partner for shipping address
                partnerShipping = Partner.create(self, orderShipping)

            # ORDER LINES
            order_line = []
            for item in order.get('line_items', []):
                sku = item.get('sku')
                product = Product.find_by_sku(self, sku, item)
                order_line = [(0, 0, {
                    'product_id': product.id,
                    'product_uom_qty': item.get('quantity', 1),
                    'price_unit': float(item.get('price', 0.0)),
                })]

            # CREATE ORDER
            order = env['sale.order'].create({
                'name': orderName,
                #'created_date': createdAt,
                'partner_id': partner,
                'partner_invoice_id': partner,
                # add shipping partner if different
                'partner_shipping_id': partnerShipping,
                'order_line': order_line,
                'currency_id': env['res.currency'].search([('name', '=', order.get("currency"))], limit=1).id,
                'state': SaleOrder.switchOrderStatus(self, order.get("status", "draft")),
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
