{
    'name': 'WooDoo',
    'version': '18.0.20250819.4',
    'summary': 'WooDoo is an Odoo ERP module that syncs data between Odoo and WordPress+WooCommerce webshop.',
    'category': 'Sales',
    'author': 'Harkály Gergő',
    'maintainer': 'Harkály Gergő',
    'company': 'brandcom.',
    'website': 'https://github.com/harkalygergo/WooDoo',
    'license': 'LGPL-3',
    'data': [
        #'security/ir.model.access.csv',  # Add this if you have security rules
        #'data/cron.xml',
        #'views/hello_world_template.xml',
        #'views/res_config_settings_views.xml',
        #'views/woodoo_sync_views.xml',
        #'data/woodoo_data.xml',
    ],
    'depends': [
        'base',
        'sale',
        'stock',
        'account',
        'contacts',
        'product',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'description': """
WooDoo - WooCommerce Integration
================================

This module provides seamless synchronization between WordPress/WooCommerce webshop and Odoo ERP.

Features:
---------
* Synchronize customers between WooCommerce and Odoo
* Sync orders from WooCommerce to Odoo
* Product synchronization
* Real-time or scheduled synchronization
* Configurable connection parameters

Requirements:
-------------
* WordPress with WooCommerce plugin
* WooCommerce REST API enabled
* Valid API credentials

Configuration:
--------------
Go to Settings > Technical > Parameters > System Parameters to configure:
* WordPress URL
* WooCommerce API Consumer Key
* WooCommerce API Consumer Secret
    """,
    #'depends': [
    #    'base',
    #    'sale',
    #    'stock',
    #    'product',
    #    'website_sale',
    #],
    #'data': [
        #'security/ir.model.access.csv',
        #'views/woo_connector_menus.xml',
        #'views/woo_product_view.xml',
        #'views/woo_order_view.xml',
        #'views/woo_connector_menus.xml',
        #'views/hello_template.xml',
        # Add more XML views if you have them
    #],
    #'assets': {
     #   'web.assets_backend': [
     #       'woo_connector/static/src/js/woo_connector.js',
     #       'woo_connector/static/src/css/woo_connector.css',
     #   ],
     #   'web.assets_frontend': [
     #       'woo_connector/static/src/css/woo_connector_frontend.css',
     #   ],
    #},
}
