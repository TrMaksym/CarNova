import random
import time
from camoufox.sync_api import Camoufox
from curl_cffi import requests
import re
import os
import urllib3
from dotenv import load_dotenv

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
load_dotenv()


class AutoRiaParser:
    def __init__(self):
        self.api_url = "https://auto.ria.com/bff/search/public/form/api"
        print("LOG: Запуск захищеного браузера Camoufox...")

        self.browser_context = Camoufox(headless=True)
        self.browser = self.browser_context.start()
        self.page = self.browser.new_page()

        try:
            self.page.goto("https://auto.ria.com/uk/", timeout=30000)
            time.sleep(2)
        except Exception as e:
            print(f"LOG: Помилка прогріву браузера: {e}")

    def check_car_details(self, car_url):
        dtp_status = "Ні"
        imported_from = "Офіціал (Україна) 🇺🇦"
        damage_comment = "Не виявлено"

        try:
            self.page.goto(car_url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(random.uniform(2.0, 3.0))

            page_text = self.page.locator("body").inner_text()
            page_text_lower = page_text.lower()

            if any(x in page_text_lower for x in ["зафіксовано дтп", "був у дтп", "був в дтп", "пошкодження"]):
                dtp_status = "Так, був у ДТП ⚠️"

            if "copart" in page_text_lower or "iaai" in page_text_lower or "аукціон сша" in page_text_lower:
                imported_from = "США 🇺🇸 (Аукціон)"
            else:
                country_match = re.search(
                    r"(?:пригнаний|імпортований|доставлений)\s+(?:з|із|в)\s+([А-ЯІЇЄҐ][а-яіїєґ\w]+)", page_text
                )

                if country_match:
                    country_name = country_match.group(1).strip()

                    flags = {
                        "Німеччини": "Німеччина 🇩🇪", "Франції": "Франція 🇫🇷", "Польщі": "Польща 🇵🇱",
                        "Італії": "Італія 🇮🇹", "США": "США 🇺🇸", "Канади": "Канада 🇨🇦",
                        "Японії": "Японія 🇯🇵", "Кореї": "Корея 🇰🇷", "Китаю": "Китай 🇨🇳",
                        "Швеції": "Швеція 🇸🇪", "Нідерландів": "Нідерланди 🇳🇱", "Бельгії": "Бельгія 🇧🇪",
                        "Швейцарії": "Швейцарія 🇨🇭", "Грузії": "Грузія 🇬🇪", "ОАЕ": "ОАЕ 🇦🇪"
                    }
                    imported_from = flags.get(country_name, f"Пригін з: {country_name}")

                elif any(x in page_text_lower for x in ["офіційне авто", "куплений в україні", "офіціал"]):
                    imported_from = "Офіціал (Україна) 🇺🇦"
                else:
                    imported_from = "Не вказано"

            desc_el = self.page.query_selector("#description, [class*='description'], #full-description")
            if desc_el:
                desc_text = desc_el.inner_text().strip()
                desc_text_lower = desc_text.lower()

                damage_keywords = [
                    "ушкоджен", "пошкоджен", "підкрас", "царапин", "косметик", "скол",
                    "притер", "вм'ятин", "вмятин", "бите", "рихтов", "фарбован", "потертост",
                    "крило", "бампер", "двері", "капот", "замінено", "мінялось", "коцни"
                ]

                if any(kw in desc_text_lower for kw in damage_keywords):
                    sentences = re.split(r'[.!?\n]', desc_text)
                    matched_sentences = []

                    for sentence in sentences:
                        if any(kw in sentence.lower() for kw in damage_keywords):
                            s_clean = sentence.strip()
                            if s_clean and s_clean not in matched_sentences:
                                matched_sentences.append(s_clean)

                    if matched_sentences:
                        damage_comment = " | ".join(matched_sentences[:3])
                        if len(damage_comment) > 150:
                            damage_comment = damage_comment[:150] + "..."
                    else:
                        damage_comment = desc_text[:100] + "..."

        except Exception as e:
            print(f"LOG: не вдалось автоматично перевірити картку: {e}")

        return dtp_status, imported_from, damage_comment


    def get_new_ads(self, brand_id, model_id=None):
        if not brand_id:
            return []

        base_url = "https://auto.ria.com/uk/search/"
        params = [
            "categories.main.id=1",
            f"brand.id[0]={brand_id}",
            "sort[0].order=date.created.desc"
        ]

        if model_id and str(model_id).strip():
            params.append(f"model.id[0]={model_id}")

        search_page_url = f"{base_url}?{'&'.join(params)}"

        try:
            print(f"\nLOG: Перехід на сторінку пошуку: {search_page_url}")
            self.page.goto(search_page_url, wait_until="domcontentloaded", timeout=60000)

            time.sleep(random.uniform(4, 6))
            self.page.evaluate("window.scrollTo(0, 600);")
            time.sleep(1)

            elements = self.page.query_selector_all(
                "section.ticket-item, .ticket-item, [data-id^='ticket-'], [data-car-id]"
            )

            ads_list = []
            for el in elements:
                try:
                    raw_id = el.get_attribute("data-id") or el.get_attribute("data-car-id") or ""
                    if not raw_id:
                        link_with_id = el.query_selector("[data-car-id], a[href*='auto____']")
                        if link_with_id:
                            raw_id = link_with_id.get_attribute("data-car-id") or link_with_id.get_attribute("id") or ""

                    ad_id = "".join(filter(str.isdigit, raw_id))

                    if not ad_id or any(ad['id'] == ad_id for ad in ads_list):
                        continue

                    title_el = el.query_selector("a[href*='/auto_'], [class*='title'], h3 a")
                    title = title_el.inner_text().strip() if title_el else "Автомобіль"

                    price = "???"
                    price_el = el.query_selector("span.green, .green, [class*='price'] b, [class*='price-ticket'] b")
                    if not price_el:
                        price_el = el.query_selector("b:has-text('$'), span:has-text('$')")

                    if price_el:
                        price_text = price_el.inner_text().strip()
                        if "$" in price_text:
                            price_text = price_text.split("$")[0]
                        price = "".join(filter(str.isdigit, price_text))

                    city = "Не вказано"
                    mileage = "0" if "нов" in title.lower() else "???"

                    rows = el.query_selector_all("div[class*='structure-row']:not([class*='labels'])")
                    for row in rows:
                        row_text = row.inner_text().strip()
                        if not row_text:
                            continue

                        row_text_lower = row_text.lower()

                        if "тис. км" in row_text_lower:
                            mileage = "".join(c for c in row_text if c.isdigit())

                        elif not any(x in row_text_lower for x in [
                            "тис. км", "бензин", "дизель", "газ", "автомат", "механіка", "гібрид", "електро", "л.",
                            "л ", "к.с.", "тому", "день", "дні", "днів", "годин", "щойно", "топ", "top",
                            "кредит", "торг", "обмін", "доставка", "перевірок", "перевірений", "реєстрації", "курс"
                        ]):
                            if not any(str(yr) in row_text for yr in range(1990, 2027)) and "грн" not in row_text_lower:
                                city = row_text.split("•")[0].strip()

                    if city in ["Не вказано", ""] or "топ" in city.lower():
                        city_el = el.query_selector("[class*='location'], [class*='address'], .js-location")
                        if city_el:
                            city_raw = city_el.inner_text().strip()
                            if not any(x in city_raw.lower() for x in ["топ", "днів"]):
                                city = city_raw.split("•")[0].split("(")[0].strip()

                    ads_list.append({
                        'id': ad_id,
                        'price': price,
                        'title': title,
                        'city': city,
                        'mileage': mileage,
                        'url': f"https://auto.ria.com/uk/auto____{ad_id}.html"
                    })
                except Exception:
                    continue

            print(f"LOG: Сторінку пропарсено. Знайдено: {len(ads_list)}")
            return ads_list

        except Exception as e:
            print(f"❌ Помилка парсингу: {e}")
            return []

    def __del__(self):
        try:
            self.browser.close()
            self.browser_context.stop()
        except:
            pass


if __name__ == "__main__":
    parser = AutoRiaParser()
    found_ads = parser.get_new_ads(brand_id="9")
    print(f"Знайдено: {len(found_ads)} авто")