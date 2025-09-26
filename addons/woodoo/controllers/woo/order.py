import json
import os
from pprint import pprint

from odoo import http, api
from addons.woodoo.controllers.woo.api import WooAPI
from addons.woodoo.controllers.woo.partner import Partner
from addons.woodoo.controllers.woo.product import Product


class Orders(http.Controller):
    @http.route('/woodoo/woo/orders/show', auth='public')
    def show(self):
        orders = self.get()
        self.sync(orders)

        """
        # call modifyWooProduct for a specific product ID with sample data
        sample_product_id = 8335  # Replace with an actual product ID
        sample_data = {
            "regular_price": "19.99",  # Example data to update the product price
            "short_description": "Updated product description"  # Example data to update the product description
        }
        updated_product = self.modifyWooProduct(sample_product_id, sample_data)
        print("Updated Product:", updated_product)
        exit()
        """

        return http.Response(
            json.dumps(orders),
            content_type='application/json; charset=utf-8'
        )

    def get_new_orders(self, max_orders=5):
        #pprint("========================= WooDoo cron get_new_orders() start ========================= ")
        try:
            #pprint("========================= WooDoo cron get_new_orders() try ========================= ")
            orders = self.get()
            self.sync(orders)
            #pprint("========================= WooDoo cron get_new_orders() ready ========================= ")
            return True
        except Exception as e:
            print("Error:", e)
            return False

    def sync(self, orders):
        try:
            for order in orders:
                self.create(order)
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
                orders = response.json()
                if isinstance(orders, list):
                    return orders
                else:
                    print("Unexpected response:", orders)
        except Exception as e:
            print("Error:", e)

    def create(self, order):
        try:
            orderName = f"WOO-{os.getenv('WP_URL')}-{order.get('id')}"
            # check if order already exists by name
            env = api.Environment(http.request.cr, http.request.uid, {})
            existingOrder = env['sale.order'].search([('name', '=', orderName)], limit=1)
            if existingOrder:
                return print("Order already exists:", existingOrder.name)

            orderBilling = order.get('billing')
            orderBillingEmail = order.get('billing').get("email")
            if not orderBillingEmail:
                return print("No billing email found for order:", order.get("id"))
            # find partner by email
            partnerId = Partner.find_by_email(self, orderBilling, orderBillingEmail)
            """
            orderShipping = order.get('shipping')
            # check if shipping address is different then billing address
            if orderShipping and orderShipping.get("address_1") and orderShipping.get("address_1") != orderBilling.get("address_1"):

                # if different, update partner with shipping address
                env = api.Environment(http.request.cr, http.request.uid, {})
                partner = env['res.partner'].browse(partnerId)
                partner.write({
                    'street': orderShipping.get('address_1', ''),
                    'street2': orderShipping.get('address_2', ''),
                    'city': orderShipping.get('city', ''),
                    'zip': orderShipping.get('postcode', ''),
                    'country_id': Partner.get_country_id(self, orderShipping.get('country')),
                })
            """
            if not partnerId:
                return print("No partner found for email:", orderBillingEmail)
            env = api.Environment(http.request.cr, http.request.uid, {})
            # loop through order.line_items and check if product exists by SKU, if not create it
            order_line = []
            for item in order.get('line_items', []):
                sku = item.get('sku')
                product = Product.find_by_sku(self, sku, item)
                order_line = [(0, 0, {
                    'product_id': product.id,
                    'product_uom_qty': item.get('quantity', 1),
                    'price_unit': float(item.get('price', 0.0)),
                })]

            order = env['sale.order'].create({
                'name': orderName,
                #'created_date': createdAt,
                'partner_id': partnerId,
                'order_line': order_line,
                'currency_id': env['res.currency'].search([('name', '=', order.get("currency"))], limit=1).id,
                'state': Orders.switchOrderStatus(self, order.get("status", "draft")),
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
