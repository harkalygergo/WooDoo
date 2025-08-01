{
    'name': 'WooCommerce Connector',
    'version': '18.0.1.0.0',
    'summary': 'Bi-directional sync between Odoo and WooCommerce',
    'description': """
WooCommerce Connector
======================
- Sync products and product images
- Sync customers
- Sync sales orders
- Continuous update between WooCommerce and Odoo
    """,
    'category': 'Connector',
    'author': 'Your Company',
    'website': 'https://yourwebsite.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'sale',
        'stock',
        'product',
        'website_sale',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/woo_connector_menus.xml',
        'views/woo_product_view.xml',
        'views/woo_order_view.xml',
        # Add more XML views if you have them
    ],
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
