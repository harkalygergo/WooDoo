# Odoo - WordPress module
###### Version: 2025.08.01.2

This module allows you to connect your Odoo instance with a WordPress site.

## How to use?

```bash
docker-compose up -d
```

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
