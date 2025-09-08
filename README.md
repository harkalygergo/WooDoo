# WooDoo

WooDoo is an Odoo ERP module that syncs data between Odoo and WordPress+WooCommerce webshop.

## Requirements

- Odoo 12 or Odoo 18
- WordPress + WooCommerce webshop
- WooCommerce API keys (Consumer Key and Consumer Secret)
- Python 3 with `requests` and `woocommerce` packages installed
- WooCommerce package: `pip install woocommerce`


## How to use?

```bash
# start Odoo 12 in Docker
docker compose -f ./docker-compose-odoo12.yml -p odoo12 up -d
# start Odoo 14 in Docker
docker compose -f ./docker-compose-odoo18.yml -p odoo18 up -d
```

---

## Documentation

All the information about the module can be found in the module's documentation: `addons/woodoo/static/description/index.html` or in the Odoo Dashboard App Information tab.

---

```bash
docker stop odoo && docker rm odoo

docker run -d --name odoo \
  --network odoo-net \
  -p 8069:8069 \
  -v ~/odoo/addons:/mnt/extra-addons \
  -e HOST=db \
  -e USER=odoo \
  -e PASSWORD=odoo \
  odoo:latest

docker exec -it odoo ls -la /mnt/extra-addons
```

---

## Help

- https://github.com/cubells/connector-woocommerce
- https://github.com/cubells/connector-woocommerce/tree/12.0-mig_connector_woocommerce

## License

Made with 💚 in Hungary by Gergő Harkály (https://www.harkalygergo.hu).
