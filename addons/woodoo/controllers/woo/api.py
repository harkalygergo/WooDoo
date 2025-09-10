import os
import urllib3
from dotenv import load_dotenv
from woocommerce import API

class WooAPI:
    def get(self):
        load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../../../../config/.env'))
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        return API(
            url=os.getenv("WP_URL"),
            consumer_key=os.getenv("WC_CONSUMER_KEY"),
            consumer_secret=os.getenv("WC_CONSUMER_SECRET"),
            version="wc/v3",
            timeout=30,
            verify_ssl=False
        )
