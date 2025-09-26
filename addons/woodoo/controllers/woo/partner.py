from odoo import http, api


class Partner():
    def __init__(self, env):
        self.env = env

    # find partner by email
    def find_by_email(self, email)  -> object | bool:
        partner = self.env['res.partner'].search([('email', '=', email)], limit=1)
        if partner:
            return partner
        else:
            return False
            #return Partner.create(self, env, billing)

    def create(self, partnerObject) -> object:
        print("partnerObject")
        print(partnerObject)
        # create new partner
        partner = self.env['res.partner'].create({
            'name': f"{partnerObject.get('first_name', '')} {partnerObject.get('last_name', '')}".strip() or "Unknown",
            'email': partnerObject.get("email", ''),
            'phone': partnerObject.get('phone', ''),
            'street': partnerObject.get('address_1', ''),
            'street2': partnerObject.get('address_2', ''),
            'city': partnerObject.get('city', ''),
            'zip': partnerObject.get('postcode', ''),
            'country_id': Partner.get_country_id_by_country_code(self, partnerObject.get('country')),
            'customer_rank': 1, # Mark as customer
            'is_company': False,
            'type': 'contact',
        })
        return partner

    def get_country_id_by_country_code(self, country_code) -> int | bool:
        if not country_code:
            return False
        country = self.env['res.country'].search([('code', '=', country_code)], limit=1)
        if country:
            return country.id
        return False
