import json
from odoo import models, api
from addons.woodoo.controllers.woo.api import WooAPI


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def write(self, vals):

        for record in self:
            default_code = record.default_code if record.default_code else ""
            # check if default_code is not empty
            if default_code:
                try:
                    data = {
                        "id": default_code,
                        "name": str(vals.get('name', record.name)),
                        "regular_price": str(vals.get('standard_price', record.standard_price)),
                        "short_description": str(vals.get('description', record.description))
                    }
                    print(json.dumps(data, indent=4))  # Pretty print the data being sent

                    wooAPI = WooAPI.get(self)
                    response = wooAPI.put(f"products/{default_code}", data)
                    if response.status_code != 200:
                        print("API error:", response.status_code, response.text)
                    else:
                        print(json.dumps(response.json(), indent=4))
                except Exception as e:
                    print("Error:", e)
