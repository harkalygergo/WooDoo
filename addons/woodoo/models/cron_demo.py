from odoo import api, models, fields
from pprint import pprint
from addons.woodoo.controllers.woo.api import WooAPI
from addons.woodoo.controllers.woo.order import Orders


class CronDemo(models.Model):
    _name = 'cron.demo'
    _description = 'Demo Model for Cron Jobs'
    parent_id = fields.Many2one('cron.demo', string='Parent')
    name = fields.Char(string='Name', required=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)

    @api.model
    def run_demo_cron(self, max_orders=5):
        pprint("=== WooDoo cron ===")
        pprint("=== WooDoo cron get_new_orders() start ===")
        try:
            pprint("=== WooDoo cron get_new_orders() try ===")
            #orders = self.get(self)
            #self.sync(orders)
            pprint("=== WooDoo cron get_new_orders() ready ===")
            return True
        except Exception as e:
            print("Error:", e)
            return False

    def get(self, max_orders):
        try:
            wooAPI = WooAPI.get(self)
            response = wooAPI.get("orders", params={"per_page": max_orders})
            pprint("=== response.status_code ===" + str(response.status_code))

            if response.status_code != 200:
                return print("API error:", response.status_code, response.text)
            else:
                orders = response.json()
                pprint("=== orders ===" + str(orders))
                if isinstance(orders, list):
                    return orders
                else:
                    print("Unexpected response:", orders)
        except Exception as e:
            print("Error:", e)

    def sync(self, orders):
        try:
            for order in orders:
                Orders.create(self, order)
            return True
        except Exception as e:
            print("Error:", e)
            return False
