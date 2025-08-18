# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import requests
import logging
import json
from datetime import datetime

_logger = logging.getLogger(__name__)


class WoodooSyncService(models.Model):
    _name = 'woodoo.sync.service'
    _description = 'WooDoo Synchronization Service'

    name = fields.Char(string='Sync Name', default='WooCommerce Sync')
    state = fields.Selection([
        ('idle', 'Idle'),
        ('running', 'Running'),
        ('error', 'Error'),
    ], default='idle', string='Status')

    last_sync_date = fields.Datetime(string='Last Sync Date')
    last_error = fields.Text(string='Last Error')
    sync_log_ids = fields.One2many('woodoo.sync.log', 'sync_service_id', string='Sync Logs')

    def _get_woocommerce_auth(self):
        """Get WooCommerce API authentication"""
        IrConfigParameter = self.env['ir.config_parameter'].sudo()

        consumer_key = IrConfigParameter.get_param('woodoo.api_consumer_key')
        consumer_secret = IrConfigParameter.get_param('woodoo.api_consumer_secret')

        if not consumer_key or not consumer_secret:
            raise UserError(
                _('WooCommerce API credentials not configured. Please go to Settings > WooDoo Configuration.'))

        return (consumer_key, consumer_secret)

    def _get_wordpress_url(self):
        """Get WordPress base URL"""
        IrConfigParameter = self.env['ir.config_parameter'].sudo()
        url = IrConfigParameter.get_param('woodoo.wordpress_url')

        if not url:
            raise UserError(_('WordPress URL not configured. Please go to Settings > WooDoo Configuration.'))

        return url.rstrip('/')

    def _make_api_request(self, endpoint, method='GET', data=None, params=None):
        """Make API request to WooCommerce"""
        try:
            base_url = self._get_wordpress_url()
            auth = self._get_woocommerce_auth()

            url = f"{base_url}/wp-json/wc/v3/{endpoint}"

            kwargs = {
                'auth': auth,
                'timeout': 30,
                'headers': {'Content-Type': 'application/json'}
            }

            if params:
                kwargs['params'] = params
            if data:
                kwargs['json'] = data

            if method == 'GET':
                response = requests.get(url, **kwargs)
            elif method == 'POST':
                response = requests.post(url, **kwargs)
            elif method == 'PUT':
                response = requests.put(url, **kwargs)
            else:
                raise UserError(_('Unsupported HTTP method: %s') % method)

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            error_msg = f"API Request failed: {str(e)}"
            _logger.error(error_msg)
            self._log_sync_error(error_msg)
            raise UserError(error_msg)

    def _log_sync_error(self, error_message):
        """Log synchronization error"""
        self.last_error = error_message
        self.state = 'error'

        self.env['woodoo.sync.log'].create({
            'sync_service_id': self.id,
            'sync_type': 'error',
            'message': error_message,
            'sync_date': fields.Datetime.now(),
        })

    def _log_sync_success(self, sync_type, message, records_count=0):
        """Log successful synchronization"""
        self.env['woodoo.sync.log'].create({
            'sync_service_id': self.id,
            'sync_type': sync_type,
            'message': message,
            'records_count': records_count,
            'sync_date': fields.Datetime.now(),
        })

    @api.model
    def sync_customers(self):
        """Sync customers from WooCommerce to Odoo"""
        IrConfigParameter = self.env['ir.config_parameter'].sudo()

        if not IrConfigParameter.get_param('woodoo.sync_customers', False):
            return {'success': True, 'message': 'Customer sync disabled'}

        try:
            _logger.info("Starting customer synchronization...")

            # Get customers from WooCommerce
            customers_data = self._make_api_request('customers', params={'per_page': 100})

            synced_count = 0
            for customer in customers_data:
                self._sync_single_customer(customer)
                synced_count += 1

            message = f"Successfully synced {synced_count} customers"
            self._log_sync_success('customers', message, synced_count)
            _logger.info(message)

            return {'success': True, 'message': message, 'count': synced_count}

        except Exception as e:
            error_msg = f"Customer sync failed: {str(e)}"
            _logger.error(error_msg)
            self._log_sync_error(error_msg)
            return {'success': False, 'message': error_msg}

    def _sync_single_customer(self, wc_customer):
        """Sync a single customer from WooCommerce data"""
        ResPartner = self.env['res.partner']

        # Check if customer already exists
        existing_partner = ResPartner.search([
            ('email', '=', wc_customer.get('email')),
        ], limit=1)

        # Prepare customer data
        partner_vals = {
            'name': f"{wc_customer.get('first_name', '')} {wc_customer.get('last_name', '')}".strip(),
            'email': wc_customer.get('email'),
            'phone': wc_customer.get('billing', {}).get('phone'),
            'is_company': False,
            'customer_rank': 1,
            'supplier_rank': 0,
            'comment': f"Imported from WooCommerce (ID: {wc_customer.get('id')})",
        }

        # Handle billing address
        billing = wc_customer.get('billing', {})
        if billing:
            partner_vals.update({
                'street': billing.get('address_1'),
                'street2': billing.get('address_2'),
                'city': billing.get('city'),
                'zip': billing.get('postcode'),
                'country_id': self._get_country_id(billing.get('country')),
                'state_id': self._get_state_id(billing.get('state'), billing.get('country')),
            })

        if existing_partner:
            existing_partner.write(partner_vals)
            _logger.debug(f"Updated existing customer: {partner_vals['name']}")
        else:
            ResPartner.create(partner_vals)
            _logger.debug(f"Created new customer: {partner_vals['name']}")

    def _get_country_id(self, country_code):
        """Get Odoo country ID from country code"""
        if not country_code:
            return False

        country = self.env['res.country'].search([('code', '=', country_code.upper())], limit=1)
        return country.id if country else False

    def _get_state_id(self, state_code, country_code):
        """Get Odoo state ID from state and country codes"""
        if not state_code or not country_code:
            return False

        country_id = self._get_country_id(country_code)
        if not country_id:
            return False

        state = self.env['res.country.state'].search([
            ('code', '=', state_code.upper()),
            ('country_id', '=', country_id)
        ], limit=1)

        return state.id if state else False

    @api.model
    def sync_orders(self):
        """Sync orders from WooCommerce to Odoo"""
        # This will be implemented in future iterations
        return {'success': True, 'message': 'Order sync not yet implemented'}

    @api.model
    def sync_products(self):
        """Sync products between WooCommerce and Odoo"""
        # This will be implemented in future iterations
        return {'success': True, 'message': 'Product sync not yet implemented'}

    @api.model
    def sync_all(self):
        """Perform full synchronization"""
        self.state = 'running'

        try:
            results = {
                'customers': self.sync_customers(),
                'orders': self.sync_orders(),
                'products': self.sync_products(),
            }

            self.state = 'idle'
            self.last_sync_date = fields.Datetime.now()

            # Count successful syncs
            total_synced = sum([r.get('count', 0) for r in results.values() if r.get('success')])

            message = f"Synchronization completed. Total records: {total_synced}"
            return {'success': True, 'message': message, 'details': results}

        except Exception as e:
            error_msg = f"Full sync failed: {str(e)}"
            self._log_sync_error(error_msg)
            return {'success': False, 'message': error_msg}


class WoodooSyncLog(models.Model):
    _name = 'woodoo.sync.log'
    _description = 'WooDoo Synchronization Log'
    _order = 'sync_date desc'

    sync_service_id = fields.Many2one('woodoo.sync.service', string='Sync Service', ondelete='cascade')
    sync_type = fields.Selection([
        ('customers', 'Customers'),
        ('orders', 'Orders'),
        ('products', 'Products'),
        ('error', 'Error'),
        ('info', 'Information'),
    ], string='Sync Type', required=True)

    message = fields.Text(string='Message', required=True)
    records_count = fields.Integer(string='Records Count', default=0)
    sync_date = fields.Datetime(string='Sync Date', default=fields.Datetime.now, required=True)

    def name_get(self):
        result = []
        for record in self:
            name = f"[{record.sync_date}] {record.sync_type}: {record.message[:50]}..."
            result.append((record.id, name))
        return result
