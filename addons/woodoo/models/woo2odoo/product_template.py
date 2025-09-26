from odoo import api, http, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.product'

    def __init__(self, env):
        self.env = env

    def find_by_default_code_woo_product_id(self, woo_product_id, item):
        product = self.env['product.product'].search([('default_code', '=', woo_product_id)], limit=1)
        if product:
            return product
        else:
            return self.create(item)

    def create(self, product_data):
        try:
            new_product = self.env['product.product'].create({
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
