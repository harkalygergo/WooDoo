from odoo import models, fields

class WooConfig(models.Model):
    _name = "woo.config"
    _description = "WooCommerce Configuration"

    name = fields.Char(default="Default Woo Store")
    woo_url = fields.Char("Store URL", required=True)
    consumer_key = fields.Char("Consumer Key", required=True)
    consumer_secret = fields.Char("Consumer Secret", required=True)
    api_version = fields.Selection(
        [("wc/v3", "WooCommerce v3")],
        default="wc/v3",
    )
    auto_sync = fields.Boolean("Enable Auto Sync", default=True)
