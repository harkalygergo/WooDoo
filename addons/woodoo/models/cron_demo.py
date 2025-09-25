from odoo import api, models, fields
import logging
from pprint import pprint

from addons.woodoo.controllers.logger import Logger

class CronDemo(models.Model):
    _name = 'cron.demo'
    _description = 'Demo Model for Cron Jobs'

    @api.model
    def run_demo_cron(self, max_orders=5):
        pprint("========================= WooDoo cron ========================= ")
