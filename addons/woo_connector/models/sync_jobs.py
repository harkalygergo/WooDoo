import requests
from odoo import models, fields, api
from odoo.addons.queue_job.job import job

class WooSync(models.Model):
    _name = "woo.sync"
    _description = "WooCommerce Synchronization Engine"

    config_id = fields.Many2one("woo.config", required=True)

    def _auth(self):
        return (self.config_id.consumer_key, self.config_id.consumer_secret)

    def _base_url(self, endpoint):
        return f"{self.config_id.woo_url}/wp-json/{self.config_id.api_version}/{endpoint}"

    # ------------------- Products -------------------
    @job
    def export_products(self):
        for prod in self.env["product.template"].search([]):
            payload = {
                "name": prod.name,
                "sku": prod.default_code,
                "regular_price": str(prod.list_price),
                "description": prod.description_sale or "",
            }
            if prod.image_1920:
                image_url = prod.image_1920_url  # requires web.base.url addon
                payload["images"] = [{"src": image_url}]
            requests.post(self._base_url("products"), auth=self._auth(), json=payload)

    @job
    def import_products(self):
        resp = requests.get(self._base_url("products"), auth=self._auth())
        for wp_prod in resp.json():
            product = self.env["product.template"].search([("default_code", "=", wp_prod["sku"])], limit=1)
            if not product:
                product = self.env["product.template"].create({
                    "name": wp_prod["name"],
                    "list_price": float(wp_prod.get("regular_price") or 0),
                    "default_code": wp_prod.get("sku"),
                })
            if wp_prod.get("images"):
                # optional: download and store image
                pass

    # ------------------- Customers -------------------
    @job
    def import_customers(self):
        resp = requests.get(self._base_url("customers"), auth=self._auth())
        for wp_cust in resp.json():
            partner = self.env["res.partner"].search([("email", "=", wp_cust["email"])], limit=1)
            if not partner:
                self.env["res.partner"].create({
                    "name": f"{wp_cust['first_name']} {wp_cust['last_name']}",
                    "email": wp_cust["email"],
                    "phone": wp_cust.get("billing", {}).get("phone"),
                    "street": wp_cust.get("billing", {}).get("address_1"),
                    "city": wp_cust.get("billing", {}).get("city"),
                    "zip": wp_cust.get("billing", {}).get("postcode"),
                })

    # ------------------- Orders -------------------
    @job
    def import_orders(self):
        resp = requests.get(self._base_url("orders"), auth=self._auth())
        for order in resp.json():
            existing = self.env["sale.order"].search([("woo_id", "=", order["id"])], limit=1)
            if existing:
                continue
            partner = self.env["res.partner"].search([("email", "=", order["billing"]["email"])], limit=1)
            if not partner:
                partner = self.env["res.partner"].create({
                    "name": f"{order['billing']['first_name']} {order['billing']['last_name']}",
                    "email": order["billing"]["email"],
                })
            so = self.env["sale.order"].create({
                "partner_id": partner.id,
                "woo_id": order["id"],
                "note": f"Woo order #{order['id']}",
            })
            for line in order["line_items"]:
                product = self.env["product.product"].search([("default_code", "=", line["sku"])], limit=1)
                if product:
                    self.env["sale.order.line"].create({
                        "order_id": so.id,
                        "product_id": product.id,
                        "product_uom_qty": line["quantity"],
                        "price_unit": float(line["price"]),
                    })
