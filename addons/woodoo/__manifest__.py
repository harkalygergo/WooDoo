{
    'name': 'WooDoo',
    'version': '18.0.20250805.2',
    'summary': 'WooDoo is an Odoo ERP module that syncs data between Odoo and WordPress+WooCommerce webshop.',
    'description': """
WooCommerce Connector
======================
- Sync products and product images
- Sync customers
- Sync sales orders
- Continuous update between WooCommerce and Odoo
    """,
    'category': 'WooDoo',
    'author': 'Harkály Gergő',
    'maintainer': 'Harkály Gergő',
    'company': 'brandcom.',
    'website': 'https://www.harkalygergo.hu',
    'license': 'LGPL-3',
    'depends': ['base'],
    'data': [
        'views/hello_world_template.xml',
    ],
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
    'installable': True,
    'application': True,
    'auto_install': False,
}
