import requests
import re
import os
import urllib3
from dotenv import load_dotenv

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()


class AutoRiaParser:
    def __init__(self):
        self.search_url = "https://auto.ria.com/uk/search/"
        self.params = {
            "search_type": "1",
            "category": "1",
            "brand.id[0]": "9",
            "model.id[0]": "1866",
            "abroad": "0",
            "customs_cleared": "1"
        }
        self.headers = {
            "User-Agent": os.getenv("ARIA_USER_AGENT"),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ru",
            "Referer": "https://auto.ria.com/uk/"
        }
        self.cookies = {
            "PHPSESSID": os.getenv("ARIA_PHPSESSID"),
            "nisess": os.getenv("ARIA_NISESS"),
            "ui": os.getenv("ARIA_UI")
        }

    def get_new_ads(self):
        try:
            response = requests.get(
                self.search_url,
                params=self.params,
                headers=self.headers,
                cookies=self.cookies,
                timeout=10,
                verify=False
            )

            if response.status_code == 200:
                html = response.text

                ids = re.findall(r'auto_[^"\' ]+_(\d+)\.html', html)
                if not ids:
                    ids = re.findall(r'data-id="(\d+)"', html)
                if not ids:
                    ids = re.findall(r'"id":(\d{8,})', html)

                ids = list(dict.fromkeys(ids))

                prices = re.findall(r'data-main-price="(\d+)"', html)

                if not ids:
                    with open("debug_page.html", "w", encoding="utf-8") as f:
                        f.write(html)
                    print("⚠️ ID не знайдено, зберіг сторінку в debug_page.html")

                results = []
                for i in range(len(ids)):
                    results.append({
                        "id": ids[i],
                        "price": prices[i] if i < len(prices) else "???"
                    })

                return results
            else:
                print(f"❌ Помилка: статус {response.status_code}")
                return []

        except Exception as e:
            print(f"💥 Критична помилка в парсері: {e}")
            return []


if __name__ == "__main__":
    parser = AutoRiaParser()
    found_ads = parser.get_new_ads()
    print(f"Знайдено: {len(found_ads)} авто")
    for ad in found_ads[:5]:
        print(f"ID: {ad['id']} | Price: {ad['price']}$")