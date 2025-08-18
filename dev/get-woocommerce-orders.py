from woocommerce import API
import urllib3
import os
from dotenv import load_dotenv

# use config/.env to load environment variables
load_dotenv(dotenv_path="config/.env")

# SSL warning elnyomása
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Környezeti változók
WP_URL = os.getenv("WP_URL")
WC_KEY = os.getenv("WC_CONSUMER_KEY")
WC_SECRET = os.getenv("WC_CONSUMER_SECRET")

wcapi = API(
    url=WP_URL,
    consumer_key=WC_KEY,
    consumer_secret=WC_SECRET,
    version="wc/v3",
    timeout=30,
    verify_ssl=False
)

try:
    response = wcapi.get("orders", params={"per_page": 5})
    if response.status_code != 200:
        print("API error:", response.status_code, response.text)
    else:
        orders = response.json()
        if isinstance(orders, list):
            for order in orders:
                print(f"Order ID: {order['id']} - Status: {order['status']} - Total: {order['total']}")
        else:
            print("Unexpected response:", orders)
except Exception as e:
    print("Error:", e)
