import json
from odoo import http, api
from addons.woodoo.controllers.woo.api import WooAPI


class ProductController(http.Controller):
    @http.route('/woodoo/woo/products/show', auth='public', type='http', methods=['GET'])
    def show(self, **kwargs):
        return http.Response(
            json.dumps(Product.get(self)),
            content_type='application/json; charset=utf-8'
        )

class Product():
    def find_by_sku(self, sku, item):
        env = api.Environment(http.request.cr, http.request.uid, {})
        product = env['product.product'].search([('default_code', '=', sku)], limit=1)
        if product:
            return product
        else:
            return Product.create(env, item)

    def create(env, product_data):
        try:
            new_product = env['product.product'].create({
                'name': product_data.get('name', 'Unnamed Product'),
                'default_code': product_data.get('product_id', ''),
                'list_price': float(product_data.get('price', 0.0)),
                'type': 'consu' if product_data.get('type') == 'simple' else 'service',
                'description_sale': str(product_data.get('description', '')),
                'sale_ok': True,
                'purchase_ok': True,
            })
            return new_product
        except Exception as e:
            print("Error creating product:", e)
            return None

    def get(self):
        try:
            wooAPI = WooAPI.get(self)
            response = wooAPI.get("products", params={"per_page": 50})
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

