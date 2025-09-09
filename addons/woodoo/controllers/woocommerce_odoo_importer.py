#!/usr/bin/env python3
"""
WooCommerce to Odoo Order Import Script
=====================================
This script imports orders from WooCommerce into Odoo using their respective APIs.
Requires: woocommerce, xmlrpc.client (built-in)
"""

import xmlrpc.client
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from woocommerce import API as WooCommerceAPI

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class WooCommerceOdooImporter:
    def __init__(self, woo_config: Dict, odoo_config: Dict):
        """
        Initialize the importer with WooCommerce and Odoo configurations

        Args:
            woo_config: WooCommerce API configuration
            odoo_config: Odoo connection configuration
        """
        # WooCommerce API setup
        self.woo_api = WooCommerceAPI(
            url=woo_config['url'],
            consumer_key=woo_config['consumer_key'],
            consumer_secret=woo_config['consumer_secret'],
            wp_api=woo_config.get('wp_api', True),
            version=woo_config.get('version', 'wc/v3'),
            timeout=woo_config.get('timeout', 30),
            verify_ssl=woo_config.get('verify_ssl', True)
        )

        # Odoo XML-RPC setup
        self.odoo_url = odoo_config['url']
        self.odoo_db = odoo_config['database']
        self.odoo_username = odoo_config['username']
        self.odoo_password = odoo_config['password']

        # Odoo connections
        self.odoo_common = xmlrpc.client.ServerProxy(f'{self.odoo_url}/xmlrpc/2/common')
        self.odoo_models = xmlrpc.client.ServerProxy(f'{self.odoo_url}/xmlrpc/2/object')

        # Authenticate with Odoo
        self.odoo_uid = self.odoo_common.authenticate(
            self.odoo_db, self.odoo_username, self.odoo_password, {}
        )

        if not self.odoo_uid:
            raise Exception("Failed to authenticate with Odoo")

        logger.info("Successfully connected to Odoo")

        # Cache for performance
        self.product_cache = {}
        self.partner_cache = {}
        self.country_cache = {}
        self.state_cache = {}

    def get_woocommerce_orders(self, **params) -> List[Dict]:
        """
        Fetch orders from WooCommerce

        Args:
            **params: Additional parameters for the WooCommerce API call

        Returns:
            List of WooCommerce orders
        """
        try:
            default_params = {
                'per_page': 100,
                'status': 'any'
            }
            default_params.update(params)

            response = self.woo_api.get('orders', params=default_params)

            if response.status_code == 200:
                orders = response.json()
                logger.info(f"Retrieved {len(orders)} orders from WooCommerce")
                return orders
            else:
                logger.error(f"Failed to fetch orders: {response.status_code} - {response.text}")
                return []

        except Exception as e:
            logger.error(f"Error fetching WooCommerce orders: {str(e)}")
            return []

    def odoo_search(self, model: str, domain: List, limit: Optional[int] = None) -> List[int]:
        """Search records in Odoo"""
        params = [self.odoo_db, self.odoo_uid, self.odoo_password, model, 'search', domain]
        if limit:
            params.append({'limit': limit})
        return self.odoo_models.execute_kw(*params)

    def odoo_read(self, model: str, ids: List[int], fields: List[str]) -> List[Dict]:
        """Read records from Odoo"""
        return self.odoo_models.execute_kw(
            self.odoo_db, self.odoo_uid, self.odoo_password,
            model, 'read', [ids], {'fields': fields}
        )

    def odoo_create(self, model: str, values: Dict) -> int:
        """Create record in Odoo"""
        return self.odoo_models.execute_kw(
            self.odoo_db, self.odoo_uid, self.odoo_password,
            model, 'create', [values]
        )

    def get_or_create_country(self, country_code: str) -> Optional[int]:
        return 99
        """Get or create country in Odoo"""
        if not country_code:
            return None

        if country_code in self.country_cache:
            return self.country_cache[country_code]

        country_ids = self.odoo_search('res.country', [('code', '=', country_code.upper())], 1)
        exit(json.dumps(country_ids))
        if country_ids:
            country_id = country_ids[0]
            self.country_cache[country_code] = country_id
            return country_id

        return None

    def get_or_create_state(self, state_code: str, country_id: int) -> Optional[int]:
        """Get or create state in Odoo"""
        if not state_code or not country_id:
            return None

        cache_key = f"{country_id}_{state_code}"
        if cache_key in self.state_cache:
            return self.state_cache[cache_key]

        state_ids = self.odoo_search('res.country.state', [
            ('code', '=', state_code.upper()),
            ('country_id', '=', country_id)
        ], 1)

        if state_ids:
            state_id = state_ids[0]
            self.state_cache[cache_key] = state_id
            return state_id

        return None

    def get_or_create_partner(self, woo_customer: Dict, billing_address: Dict) -> int:
        """Get or create customer in Odoo"""
        if not billing_address.get('email'):
            logger.warning("Customer has no email, using default customer")
            # Return default customer or create anonymous customer
            return self.get_default_customer()

        email = billing_address.get('email').lower()

        if email in self.partner_cache:
            return self.partner_cache[email]

        # Search for existing customer
        partner_ids = self.odoo_search('res.partner', [('email', '=', email)], 1)
        if partner_ids:
            partner_id = partner_ids[0]
            self.partner_cache[email] = partner_id
            return partner_id

        # Create new customer
        country_id = self.get_or_create_country(billing_address.get('country'))
        state_id = self.get_or_create_state(billing_address.get('state'), country_id) if country_id else None

        partner_data = {
            'name': f"{billing_address.get('first_name', '')} {billing_address.get('last_name', '')}".strip() or 'Unknown Customer',
            'email': email,
            'phone': billing_address.get('phone', ''),
            'street': billing_address.get('address_1', ''),
            'street2': billing_address.get('address_2', ''),
            'city': billing_address.get('city', ''),
            'zip': billing_address.get('postcode', ''),
            'country_id': country_id,
            'state_id': state_id,
            'is_company': False,
            'customer_rank': 1,
        }

        partner_id = self.odoo_create('res.partner', partner_data)
        self.partner_cache[email] = partner_id
        logger.info(f"Created customer: {partner_data['name']}")

        return partner_id

    def get_default_customer(self) -> int:
        """Get or create a default customer for orders without customer info"""
        partner_ids = self.odoo_search('res.partner', [('name', '=', 'WooCommerce Guest')], 1)
        if partner_ids:
            return partner_ids[0]

        partner_data = {
            'name': 'WooCommerce Guest',
            'is_company': False,
            'customer_rank': 1,
        }
        return self.odoo_create('res.partner', partner_data)

    def get_or_create_product(self, woo_line_item: Dict) -> int:
        """Get or create product in Odoo"""
        product_id = woo_line_item.get('product_id')
        sku = woo_line_item.get('sku', '')
        name = woo_line_item.get('name', 'Unknown Product')

        cache_key = f"woo_{product_id}"
        if cache_key in self.product_cache:
            return self.product_cache[cache_key]

        # Search by SKU first, then by name
        domain = []
        if sku:
            domain = [('default_code', '=', sku)]
        else:
            domain = [('name', '=', name)]

        product_ids = self.odoo_search('product.product', domain, 1)

        if product_ids:
            odoo_product_id = product_ids[0]
            self.product_cache[cache_key] = odoo_product_id
            return odoo_product_id

        # Create new product
        product_data = {
            'name': name,
            'default_code': sku if sku else f'WOO_{product_id}',
            'type': 'product',
            'sale_ok': True,
            'purchase_ok': False,
            'list_price': float(woo_line_item.get('price', 0)),
        }

        odoo_product_id = self.odoo_create('product.product', product_data)
        self.product_cache[cache_key] = odoo_product_id
        logger.info(f"Created product: {name}")

        return odoo_product_id

    def map_order_status(self, woo_status: str) -> str:
        """Map WooCommerce order status to Odoo sale order state"""
        status_mapping = {
            'pending': 'draft',
            'processing': 'sale',
            'on-hold': 'draft',
            'completed': 'sale',
            'cancelled': 'cancel',
            'refunded': 'cancel',
            'failed': 'cancel',
        }
        return status_mapping.get(woo_status, 'draft')

    def create_sale_order(self, woo_order: Dict) -> Optional[int]:
        """Create sale order in Odoo from WooCommerce order"""

        partner_id = 1
        """
        try:
            # Get or create customer
            partner_id = self.get_or_create_partner(
                woo_order.get('customer', {}),
                woo_order.get('billing', {})
            )
        except Exception as e:
            logger.error(f"ERROR get_or_create_partner {woo_order.get('id')}: {str(e)}")
            return None
        """

        try:
            # Parse date
            date_created = datetime.fromisoformat(
                woo_order['date_created'].replace('T', ' ').replace('Z', '')
            )

            # Create sale order
            order_data = {
                'partner_id': partner_id,
                'date_order': date_created.strftime('%Y-%m-%d %H:%M:%S'),
                'client_order_ref': f"WOO-{woo_order['id']}",
                'note': woo_order.get('customer_note', ''),
                'state': self.map_order_status(woo_order.get('status', 'pending')),
            }

            # Add shipping address if different from billing
            shipping_address = woo_order.get('shipping', {})
            # dump shipping_address
            #exit(json.dumps(shipping_address, indent=4))
            #exit(json.dumps(shipping_address, indent=4))
            #exit(json.dumps(woo_order.get('billing', {}), indent=4))
            #exit(shipping_address != woo_order.get('billing', {}))
            json.dumps(shipping_address.get('country'))

            if shipping_address and shipping_address != woo_order.get('billing', {}):
                #exit("Shipping address is different from billing address")
                json.dumps(shipping_address.get('country'))

                # Create delivery address
                country_id = self.get_or_create_country(shipping_address.get('country'))
                #exit(json.dumps(country_id))
                #state_id = self.get_or_create_state(shipping_address.get('state'), country_id) if country_id else None

                shipping_partner_data = {
                    'name': f"{shipping_address.get('first_name', '')} {shipping_address.get('last_name', '')}".strip(),
                    'street': shipping_address.get('address_1', ''),
                    'street2': shipping_address.get('address_2', ''),
                    'city': shipping_address.get('city', ''),
                    'zip': shipping_address.get('postcode', ''),
                    'country_id': country_id,
                    'state_id': 1,
                    'parent_id': partner_id,
                    'type': 'delivery',
                }
                shipping_partner_id = self.odoo_create('res.partner', shipping_partner_data)
                order_data['partner_shipping_id'] = shipping_partner_id
            else:
                exit("Shipping address is the same as billing address")

            sale_order_id = self.odoo_create('sale.order', order_data)
            logger.info(f"Created sale order ID: {sale_order_id} for WooCommerce order {woo_order['id']}")

            # Create order lines
            for line_item in woo_order.get('line_items', []):
                self.create_order_line(sale_order_id, line_item)

            # Handle shipping
            if float(woo_order.get('shipping_total', 0)) > 0:
                self.create_shipping_line(sale_order_id, woo_order)

            # Handle taxes
            for tax_line in woo_order.get('tax_lines', []):
                self.create_tax_line(sale_order_id, tax_line)

            return sale_order_id

        except Exception as e:
            logger.error(f"Error creating sale order for WooCommerce order {woo_order.get('id')}: {str(e)}")
            return None

    def create_order_line(self, sale_order_id: int, line_item: Dict):
        """Create sale order line"""
        try:
            product_id = self.get_or_create_product(line_item)

            line_data = {
                'order_id': sale_order_id,
                'product_id': product_id,
                'product_uom_qty': float(line_item.get('quantity', 1)),
                'price_unit': float(line_item.get('price', 0)),
                'name': line_item.get('name', 'Product'),
            }

            line_id = self.odoo_create('sale.order.line', line_data)
            logger.debug(f"Created order line: {line_data['name']}")

        except Exception as e:
            logger.error(f"Error creating order line: {str(e)}")

    def create_shipping_line(self, sale_order_id: int, woo_order: Dict):
        """Create shipping line as a service product"""
        try:
            # Get or create shipping product
            shipping_product_ids = self.odoo_search('product.product', [('default_code', '=', 'SHIPPING')], 1)

            if not shipping_product_ids:
                shipping_product_data = {
                    'name': 'Shipping',
                    'default_code': 'SHIPPING',
                    'type': 'service',
                    'sale_ok': True,
                }
                shipping_product_id = self.odoo_create('product.product', shipping_product_data)
            else:
                shipping_product_id = shipping_product_ids[0]

            shipping_line_data = {
                'order_id': sale_order_id,
                'product_id': shipping_product_id,
                'product_uom_qty': 1,
                'price_unit': float(woo_order.get('shipping_total', 0)),
                'name': 'Shipping',
            }

            self.odoo_create('sale.order.line', shipping_line_data)
            logger.debug("Created shipping line")

        except Exception as e:
            logger.error(f"Error creating shipping line: {str(e)}")

    def create_tax_line(self, sale_order_id: int, tax_line: Dict):
        """Handle tax lines - in Odoo 18, taxes are typically handled automatically"""
        # Note: In Odoo 18, taxes are usually applied automatically based on product configuration
        # and fiscal positions. Manual tax line creation is rarely needed.
        pass

    def import_orders(self, **woo_params) -> Dict[str, int]:
        """
        Import orders from WooCommerce to Odoo

        Args:
            **woo_params: Parameters to pass to WooCommerce API

        Returns:
            Dictionary with import statistics
        """
        stats = {'total': 0, 'success': 0, 'failed': 0, 'skipped': 0}

        # Get orders from WooCommerce
        woo_orders = self.get_woocommerce_orders(**woo_params)
        stats['total'] = len(woo_orders)

        for woo_order in woo_orders:
            try:
                # Check if order already exists
                woo_order_ref = f"WOO-{woo_order['id']}"
                """
                try:
                    existing_orders = self.odoo_search('sale.order', [
                        ('client_order_ref', '=', woo_order_ref)
                    ], 1)

                    if existing_orders:
                        logger.info(f"Order {woo_order_ref} already exists, skipping")
                        stats['skipped'] += 1
                        continue
                except Exception as e:
                    logger.warning(f"Error checking existing order {woo_order_ref}: {e}")
                    # Continue with import if we can't check for duplicates
                """
                # Create the order
                sale_order_id = self.create_sale_order(woo_order)
                #exit(json.dumps(sale_order_id))

                if sale_order_id:
                    stats['success'] += 1
                    logger.info(f"Successfully imported WooCommerce order {woo_order['id']}")
                else:
                    stats['failed'] += 1

            except Exception as e:
                logger.error(f"Failed to import order {woo_order.get('id')}: {str(e)}")
                stats['failed'] += 1

        return stats


def main():
    """Main function to run the import"""

    # Configuration
    woo_config = {
        'url': 'https://wordpress.local',  # Your WooCommerce store URL
        'consumer_key': 'ck_10dfec0a47803bce7088b698064ca76860de53c3',
        'consumer_secret': 'cs_8ca3f5b1a7831a814c83aaf081dae3a4b04b397e',
        'version': 'wc/v3',
        'verify_ssl': False  # Set to False for self-signed certificates
    }

    odoo_config = {
        'url': 'http://localhost:8069',  # Use http:// for local development
        'database': 'mydb',
        'username': 'admin',
        'password': 'admin',
        'verify_ssl': False  # Set to False for self-signed certificates
    }

    try:
        # Create importer instance
        importer = WooCommerceOdooImporter(woo_config, odoo_config)

        # Import parameters (optional)
        import_params = {
            'per_page': 50,  # Number of orders per request
            # 'status': 'completed',  # Try removing status filter first
            # 'after': '2024-01-01T00:00:00',  # Orders after this date
            # 'before': '2024-12-31T23:59:59',  # Orders before this date
            'orderby': 'date',  # Order by date
            'order': 'desc'  # Most recent first
        }

        # Run import
        logger.info("Starting WooCommerce to Odoo import...")
        stats = importer.import_orders(**import_params)

        # Print results
        logger.info("Import completed!")
        logger.info(f"Total orders processed: {stats['total']}")
        logger.info(f"Successfully imported: {stats['success']}")
        logger.info(f"Failed: {stats['failed']}")
        logger.info(f"Skipped (already exist): {stats['skipped']}")

    except Exception as e:
        logger.error(f"Import failed: {str(e)}")
        raise


if __name__ == '__main__':
    main()
