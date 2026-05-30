import requests
import re
import os
from dotenv import load_dotenv

load_dotenv()

class AutoRiaParser:
    def __init__(self):
        self.search_url = "https://www.autoria.com/uk/search/"
        self.params = {
            "search_type": "1",
            "category": "1",
            "all[0].any[0].brand[0]": "9",
            "all[0].any[0].any[0].model[0]": "1866",
            "abroad": "0",
            "customs_cleared": "1"
        }
        self.headers = {
            "user_agent": os.getenv("ARIA_USER_AGENT"),
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "accept-language": "ru",
            "referer": "https://auto.ria.com/uk/"
        }
        self.cookies = {
            "PHPSESSID": os.getenv("ARIA_PHPSESSID"),
            "NISSES": os.getenv("ARIA_NISSES"),
            "ui": os.getenv("ARIA_UI")
        }

    def get_new_ads(self):
        try:
            response = requests.get(
                self.search_url,
                params=self.params,
                headers=self.headers,
                cookies=self.cookies,
                timeout=10
            )

            if response.status_code == 200:

                html = response.text

                ids = re.findall(r'data-id="(\d+)"', html)
                prices = re.findall(r'data-main-price="(\d+)"', html)

                results = []
                for i in range(len(ids)):
                    results.append({
                        "id": ids[i],
                        "price": prices[i] if i < len(prices) else "???"
                    })

                return results
            else:
                print(f"Failed to fetch new ads, status code:, {response.status_code}")
                return []
        except Exception as e:
            print(f"An error occurred: {e}")
            return []



if __name__ == "__main__":
    parser = AutoRiaParser()
    ads = parser.get_new_ads()
    print(f"Found {len(ads)} new ads:")
    for ad in ads[:5]:
        print(f"ID: {ad['id']} | Price: {ad['price']}$")
