from odoo import models, api, fields
from addons.woodoo.controllers.logger import Logger
from addons.woodoo.controllers.woo.api import WooAPI


class Tax(models.AbstractModel):
    _inherit = 'account.tax'

    @api.model
    def write(self, vals):
        try:
            wooAPI = WooAPI.get(self)
            data = {
                "id": self.id,
                "name": self.name,
                "rate": str(self.amount),
            }
            Logger.log(f"Syncing VAT to WooCommerce: {data}")
            response = wooAPI.put(f"taxes/{self.id}", data)
            if response.status_code != 200:
                Logger.log(f"API error while syncing VAT: {response.status_code} {response.text}")
            else:
                Logger.log(f"Successfully synced VAT to WooCommerce: {response.json()}")
        except Exception as e:
            Logger.log(f"Error while syncing VAT to WooCommerce: {e}")

        return super(Tax, self).write(vals)
