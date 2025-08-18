# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
import requests
import logging

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # WordPress/WooCommerce Connection Settings
    woodoo_wordpress_url = fields.Char(
        string='WordPress URL',
        help='Full URL of your WordPress site (e.g., https://example.com)',
        config_parameter='woodoo.wordpress_url'
    )

    woodoo_api_consumer_key = fields.Char(
        string='WooCommerce API Consumer Key',
        help='Consumer Key from WooCommerce > Settings > Advanced > REST API',
        config_parameter='woodoo.api_consumer_key'
    )

    woodoo_api_consumer_secret = fields.Char(
        string='WooCommerce API Consumer Secret',
        help='Consumer Secret from WooCommerce > Settings > Advanced > REST API',
        config_parameter='woodoo.api_consumer_secret'
    )

    # Synchronization Settings
    woodoo_sync_customers = fields.Boolean(
        string='Sync Customers',
        default=True,
        config_parameter='woodoo.sync_customers',
        help='Enable customer synchronization from WooCommerce to Odoo'
    )

    woodoo_sync_orders = fields.Boolean(
        string='Sync Orders',
        default=True,
        config_parameter='woodoo.sync_orders',
        help='Enable order synchronization from WooCommerce to Odoo'
    )

    woodoo_sync_products = fields.Boolean(
        string='Sync Products',
        default=False,
        config_parameter='woodoo.sync_products',
        help='Enable product synchronization between WooCommerce and Odoo'
    )

    woodoo_auto_sync = fields.Boolean(
        string='Auto Sync',
        default=False,
        config_parameter='woodoo.auto_sync',
        help='Enable automatic synchronization via scheduled actions'
    )

    woodoo_sync_interval = fields.Selection([
        ('5', 'Every 5 minutes'),
        ('15', 'Every 15 minutes'),
        ('30', 'Every 30 minutes'),
        ('60', 'Every hour'),
        ('360', 'Every 6 hours'),
        ('720', 'Every 12 hours'),
        ('1440', 'Daily'),
    ], string='Sync Interval',
        default='60',
        config_parameter='woodoo.sync_interval',
        help='Interval for automatic synchronization'
    )

    # Status and Connection Info
    woodoo_connection_status = fields.Char(
        string='Connection Status',
        compute='_compute_connection_status',
        readonly=True
    )

    woodoo_last_sync = fields.Datetime(
        string='Last Sync',
        config_parameter='woodoo.last_sync',
        readonly=True
    )

    @api.depends('woodoo_wordpress_url', 'woodoo_api_consumer_key', 'woodoo_api_consumer_secret')
    def _compute_connection_status(self):
        for record in self:
            if not all(
                [record.woodoo_wordpress_url, record.woodoo_api_consumer_key, record.woodoo_api_consumer_secret]):
                record.woodoo_connection_status = 'Not Configured'
            else:
                record.woodoo_connection_status = 'Configured (Test connection to verify)'

    @api.constrains('woodoo_wordpress_url')
    def _check_wordpress_url(self):
        for record in self:
            if record.woodoo_wordpress_url:
                if not record.woodoo_wordpress_url.startswith(('http://', 'https://')):
                    raise ValidationError(_('WordPress URL must start with http:// or https://'))

    def test_woodoo_connection(self):
        """Test connection to WooCommerce API"""
        self.ensure_one()

        if not all([self.woodoo_wordpress_url, self.woodoo_api_consumer_key, self.woodoo_api_consumer_secret]):
            raise ValidationError(_('Please configure all required fields before testing connection.'))

        try:
            # Clean URL
            base_url = self.woodoo_wordpress_url.rstrip('/')
            api_url = f"{base_url}/wp-json/wc/v3/system_status"

            # Test API connection
            auth = (self.woodoo_api_consumer_key, self.woodoo_api_consumer_secret)
            response = requests.get(api_url, auth=auth, timeout=10)

            if response.status_code == 200:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Success!'),
                        'message': _('Connection to WooCommerce API successful.'),
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                _logger.error("WooCommerce connection test failed: %s", error_msg)
                raise ValidationError(_('Connection failed: %s') % error_msg)

        except requests.exceptions.RequestException as e:
            _logger.error("WooCommerce connection test error: %s", str(e))
            raise ValidationError(_('Connection error: %s') % str(e))

    def sync_now_woodoo(self):
        """Trigger immediate synchronization"""
        self.ensure_one()

        if not all([self.woodoo_wordpress_url, self.woodoo_api_consumer_key, self.woodoo_api_consumer_secret]):
            raise ValidationError(_('Please configure connection settings first.'))

        # This will be implemented in the sync service
        sync_service = self.env['woodoo.sync.service']
        try:
            result = sync_service.sync_all()

            # Update last sync time
            self.env['ir.config_parameter'].sudo().set_param('woodoo.last_sync', fields.Datetime.now())

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Sync Complete'),
                    'message': result.get('message', _('Synchronization completed successfully.')),
                    'type': 'success',
                    'sticky': False,
                }
            }
        except Exception as e:
            _logger.error("Manual sync failed: %s", str(e))
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Sync Failed'),
                    'message': str(e),
                    'type': 'danger',
                    'sticky': True,
                }
            }
