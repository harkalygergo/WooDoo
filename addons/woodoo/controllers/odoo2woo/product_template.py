import json

from odoo import models, api
from addons.woodoo.controllers.logger import Logger
from addons.woodoo.controllers.woo.api import WooAPI


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def write(self, vals):
        productTemplate = super(ProductTemplate, self).write(vals)

        for record in self:
            default_code = record.default_code if record.default_code else ""
            # check if default_code is not empty
            if default_code:
                try:
                    Logger.log(f"Updating product {default_code} with vals: {json.dumps(vals, indent=4)}")
                    # log all data of record and vals
                    Logger.log("RECORD:" + json.dumps(record.read()[0], indent=4, default=str, ensure_ascii=False))

                    data = {
                        "id": default_code,
                        "name": str(vals.get('name', record.name)),
                        "regular_price": str(vals.get('list_price', record.list_price)),
                        "description": str(vals.get('description_ecommerce', record.description_ecommerce)),
                        "short_description": str(vals.get('description', record.description)),
                        "stock_quantity": str(vals.get('qty_available', record.qty_available))
                    }
                    Logger.log(json.dumps(data, indent=4))  # Pretty print the data being sent

                    wooAPI = WooAPI.get(self)
                    response = wooAPI.put(f"products/{default_code}", data)
                    if response.status_code != 200:
                        Logger.log("API error:" + response.status_code + response.text)
                    else:
                        Logger.log(json.dumps(response.json(), indent=4))
                except Exception as e:
                    Logger.log("Error:" + json.dumps(e))

        return productTemplate
