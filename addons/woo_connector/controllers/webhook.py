from odoo import http
from odoo.http import request

class WooWebhook(http.Controller):

    @http.route('/woo/webhook', type='json', auth='public', csrf=False)
    def woo_webhook(self, **kwargs):
        payload = request.jsonrequest
        sync_engine = request.env["woo.sync"].sudo()
        if payload.get("resource") == "order":
            sync_engine.import_orders.delay()
        elif payload.get("resource") == "product":
            sync_engine.import_products.delay()
        elif payload.get("resource") == "customer":
            sync_engine.import_customers.delay()
        return {"status": "received"}
