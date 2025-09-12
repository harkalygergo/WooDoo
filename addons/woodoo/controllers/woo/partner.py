from odoo import http, api


class Partner():
    def find_by_email(self, billing, email):
        # find partner by email
        env = api.Environment(http.request.cr, http.request.uid, {})
        partner = env['res.partner'].search([('email', '=', email)], limit=1)
        if partner:
            return partner.id
        else:
            self.create(env, billing)

    def create(self, env, billing):
        # create new partner
        new_partner = env['res.partner'].create({
            'name': f"{billing.get('first_name', '')} {billing.get('last_name', '')}".strip() or "Unknown",
            'email': billing.get("email", ''),
            'phone': billing.get('phone', ''),
            'street': billing.get('address_1', ''),
            'street2': billing.get('address_2', ''),
            'city': billing.get('city', ''),
            'zip': billing.get('postcode', ''),
            'country_id': Partner.get_country_id(self, billing.get('country')),
            'customer_rank': 1,  # Mark as customer
            'is_company': False,
            'type': 'contact',
        })
        return new_partner.id

    def get_country_id(self, param):
        if not param:
            return False
        env = api.Environment(http.request.cr, http.request.uid, {})
        country = env['res.country'].search([('code', '=', param)], limit=1)
        if country:
            return country.id
        return False
