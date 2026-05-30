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
    parser = AutoRiaParser()
    seen_ids = set()

    console.print("[bold green]🚀 OmniAuto: Моніторинг ринку запущено![/bold green]")
    console.print("[yellow]Аналізую поточні оголошення...[/yellow]")

    initial_ads = parser.get_new_ads()
    for ad in initial_ads:
        seen_ids.add(ad['id'])

    console.print(f"✅ База готова. В пам'яті {len(seen_ids)} об'єктів. Стежу за оновленнями...")

    try:
        while True:
            current_ads = parser.get_new_ads()
            new_found = False

            if current_ads:

                for ad in current_ads:
                    if ad['id'] not in seen_ids:
                        console.print(f"\n[bold red]🔥 ЗНАЙДЕНО НОВУ ПРОПОЗИЦІЮ![/bold red]")
                        console.print(f"[bold white]ID:[/bold white] {ad['id']}")
                        console.print(f"[bold green]Ціна:[/bold green] {ad['price']}$")
                        console.print(f"[blue]Посилання:[/blue] https://auto.ria.com/uk/auto____{ad['id']}.html")

                        seen_ids.add(ad['id'])
                        new_found = True

                        msg = (
                            f"<b> Знайдено нове оголошення: </b>\n"
                            f"Ціна: <code>{ad['price']}$</code>\n"
                            f"🔗 <a href='https://auto.ria.com/uk/auto____{ad['id']}.html'>Переглянути на Auto.ria</a>"                        )

                        send_telegram(msg)

                        seen_ids.add(ad['id'])


                if not new_found:
                    console.print(".", end="")

                time.sleep(30)

    except KeyboardInterrupt:
        console.print("\n[bold yellow]Роботу радара припинено користувачем.[/bold yellow]")


if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_bot_polling)
    bot_thread.start()
    start_monitoring()