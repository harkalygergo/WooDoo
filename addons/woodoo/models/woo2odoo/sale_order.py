import os
from datetime import date
from odoo import api, http, fields, models
from addons.woodoo.controllers.woo.api import WooAPI
from addons.woodoo.controllers.woo.partner import Partner
#from addons.woodoo.models.woo2odoo.product_template import ProductTemplate

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def cron(self, max_orders=20):
        try:
            print("=== WooDoo SaleOrder cron start ===")
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
                "per_page": max_orders
                #"after": f"{today}T00:00:00"
            })
            if response.status_code != 200:
                return print("API error:", response.status_code, response.text)
            else:
                orders = response.json()
                print("=== WooDoo SaleOrder cron orders ===")
                print(orders)
                if isinstance(orders, list):
                    return orders
                else:
                    print("Unexpected response:", orders)
        except Exception as e:
            print("Error:", e)

    def sync(self, orders):
        try:
            for order in orders:
                self.create_order(order)
            return True
        except Exception as e:
            print("Error:", e)
            return False

    def create_order(self, order):
        try:
            print("=== WooDoo SaleOrder create order ===")
            print("order")
            print(order)
            env = self.env #api.Environment(http.request.cr, http.request.uid, {})
            orderName = f"WOO-{os.getenv('WP_URL')}-{order.get('id')}"
            print("orderName")
            print(orderName)
            # check if order already exists by name
            existingOrder = env['sale.order'].search([('name', '=', orderName)], limit=1)
            if existingOrder:
                return print("Order already exists:", existingOrder.name)

            # PARTNER
            orderBilling = order.get('billing')
            print("orderBilling")
            print(orderBilling)
            orderShipping = order.get('shipping')
            print("orderShipping")
            print(orderShipping)
            # find partner by billing email
            partner = Partner.find_by_email(self, orderBilling.get("email"))
            print("partner")
            print(partner)
            # if not found, create partner first
            if not partner:
                partner = Partner.create(self, orderBilling)
            print("partner")
            print(partner)

            # SHIPPING
            partnerShipping = partner
            # check if billing and shipping first_name, last_name, company, address_1, address_2, city, state, postcode, country, phone different
            if orderBilling.get("first_name") != orderShipping.get("first_name") or \
               orderBilling.get("last_name") != orderShipping.get("last_name") or \
               orderBilling.get("country") != orderShipping.get("country") or \
               orderBilling.get("postcode") != orderShipping.get("postcode") or \
               orderBilling.get("city") != orderShipping.get("city") or \
               orderBilling.get("state") != orderShipping.get("state") or \
               orderBilling.get("address_1") != orderShipping.get("address_1") or \
               orderBilling.get("address_2") != orderShipping.get("address_2") or \
               orderBilling.get("phone") != orderShipping.get("phone") or \
               orderBilling.get("company") != orderShipping.get("company"):
                # if different, create new partner for shipping address

                # set orderShipping email to orderBilling email if empty
                orderShipping["email"] = orderBilling.get("email")

                partnerShipping = Partner.create(self, orderShipping)
            print("partnerShipping")
            print(partnerShipping)

            # ORDER LINES
            order_line = []
            print("order_lines1")
            print(order_line)
            """
            for item in order.get('line_items', []):
                product = ProductTemplate.find_by_default_code_woo_product_id(self, item.get("id"), item)
                order_line = [(0, 0, {
                    'product_id': product.id,
                    'product_uom_qty': item.get('quantity', 1),
                    'price_unit': float(item.get('price', 0.0)),
                })]
            """
            print("order_lines2")
            print(order_line)

            # CREATE ORDER
            new_order = self.create({
                'name': orderName,
                #'created_date': createdAt,
                'partner_id':  partner.id if partner else False,
                'partner_invoice_id':  partner.id if partner else False,
                # add shipping partner if different
                'partner_shipping_id': partnerShipping.id if partnerShipping else False,
                'order_line': order_line,
                'currency_id': env['res.currency'].search([('name', '=', order.get("currency"))], limit=1).id,
                'state': SaleOrder.switchOrderStatus(self, order.get("status", "draft")),
                'amount_total': float(order.get("total", 0.0)),
            })
            print("new_order")
            print(new_order)
            exit()

            return print(f"Created Sale Order: {new_order.name}")
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
