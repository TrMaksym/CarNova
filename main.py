import os
import threading
import time
from autoria import AutoRiaParser
from rich.console import Console
from tg_bot import send_telegram, bot

console = Console()


def run_bot_polling():
    print("Бот почав слухати команди")
    bot.infinity_polling()


def start_monitoring():
    current_filter_raw = None
    parser = AutoRiaParser()
    seen_ids = set()

    active_brand_id = None
    active_model_id = None

    console.print("[bold green]🚀 OmniAuto: Моніторинг ринку запущено![/bold green]")

    try:
        while True:
            if os.path.exists("current_filter.txt"):
                try:
                    with open("current_filter.txt", "r", encoding="utf-8") as f:
                        lines = f.readlines()
                        new_filter_raw = lines[0].strip() if lines else ""

                    if new_filter_raw and new_filter_raw != current_filter_raw:
                        console.print(f"\n[bold cyan]🔄 Оновлення фільтра на: {new_filter_raw}[/bold cyan]")

                        parts = new_filter_raw.split('|')
                        active_brand_id = parts[0] if len(parts) > 0 and parts[0] else None
                        active_model_id = parts[1] if len(parts) > 1 and parts[1] else None

                        current_filter_raw = new_filter_raw
                        seen_ids.clear()
                        console.print(f"✅ Новий фільтр встановлено: Марка {active_brand_id}, Модель {active_model_id}")
                except Exception as e:
                    print(f"Помилка читання файлу конфігурації: {e}")

            if active_brand_id:
                current_ads = parser.get_new_ads(brand_id=active_brand_id, model_id=active_model_id)
                new_found = False

                if current_ads:
                    for ad in current_ads:
                        if ad['id'] not in seen_ids:
                            car_url = ad.get('url', f"https://auto.ria.com/uk/auto____{ad['id']}.html")

                            console.print(
                                f"\n[bold yellow]🔍 Знайдено нове авто ({ad['id']}). Заходимо вглиб для аналізу...[/bold yellow]")

                            car_dtp, car_imported, car_damage = parser.check_car_details(car_url)

                            console.print(f"[bold red]🔥 ОГОЛОШЕННЯ ПЕРЕВІРЕНО Й ДОДАНО![/bold red]")

                            car_title = ad.get('title', 'Авто без назви')
                            car_price = ad.get('price', '???')
                            car_mileage = ad.get('mileage', '???')
                            car_city = ad.get('city', 'Місто не вказане')

                            with open("found_cars.txt", "a", encoding="utf-8") as f:
                                f.write(f"--- {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")
                                f.write(f"Авто: {car_title}\n")
                                f.write(f"Ціна: {car_price}$\n")
                                f.write(f"Пробіг: {car_mileage} тис. км\n")
                                f.write(f"Місто: {car_city}\n")
                                f.write(f"Був у ДТП: {car_dtp}\n")
                                f.write(f"Пригнаний з: {car_imported}\n")
                                f.write(f"Нюанси з опису: {car_damage}\n")
                                f.write(f"Посилання: {car_url}\n")
                                f.write("-" * 30 + "\n")

                            msg = (
                                f"<b>🔥 Знайдено {car_title}</b>\n"
                                f"💰 Ціна: <code>{car_price}$</code>\n"
                                f"📍 Місто: {car_city}\n"
                                f"🛣️ Пробіг: {car_mileage} тис. км\n"
                                f"⚠️ ДТП (База): <b>{car_dtp}</b>\n"
                                f"🌍 Пригін: <b>{car_imported}</b>\n"
                            )

                            if car_damage != "Не виявлено":
                                msg += f"✏️ <b>З опису власника:</b> <i>«{car_damage}»</i>\n\n"
                            else:
                                msg += f"✏️ <b>З опису власника:</b> Прямих згадок дефектів немає\n\n"

                            msg += f"🔗 <a href='{car_url}'>Переглянути оголошення</a>"

                            send_telegram(msg)
                            seen_ids.add(ad['id'])
                            new_found = True

                if not new_found:
                    print(".", end="", flush=True)

            time.sleep(60)

    except KeyboardInterrupt:
        console.print("\n[bold yellow]Роботу радара припинено користувачем.[/bold yellow]")


if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_bot_polling, daemon=True)
    bot_thread.start()
    start_monitoring()