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
