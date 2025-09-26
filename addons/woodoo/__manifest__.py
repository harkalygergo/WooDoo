{
    'name': 'WooDoo',
    'version': '18.0.20250924.9',
    'summary': 'WooDoo is an Odoo ERP module that syncs data between Odoo and WordPress+WooCommerce webshop.',
    'category': 'Sales',
    'author': 'Harkály Gergő',
    'maintainer': 'Harkály Gergő',
    'company': 'brandcom.',
    'website': 'https://github.com/harkalygergo/WooDoo',
    'license': 'LGPL-3',
    'data': [
        'security/ir.model.access.csv',
        # data files first, followed by security files, and then your view files.
        "data/ir_cron.xml",
        #"data/cronjobs.xml",
        #'views/res_config_settings_view.xml',
        #'security/ir.model.access.csv',
        #'data/cron.xml',
    ],
    'depends': [
        'base',
        'sale',
        'sale_management',
        'stock',
        'account',
        'contacts',
        'product',
        'website_sale',
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
