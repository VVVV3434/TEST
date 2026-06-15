import os
import requests
import subprocess
import sys

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    print("❌ BOT_TOKEN не найден в переменных окружения")
    sys.exit()

BASE = f"https://api.telegram.org/bot{TOKEN}"

def tg(method):
    try:
        r = requests.get(f"{BASE}/{method}", timeout=20)
        print(f"\n--- {method} ---")
        print(r.text)
    except Exception as e:
        print(f"Ошибка {method}:", e)

print("Проверяю Telegram bot...")

tg("getMe")
tg("getWebhookInfo")

print("\n--- getUpdates test ---")
try:
    r = requests.get(f"{BASE}/getUpdates", timeout=20)
    print(r.text)
except Exception as e:
    print("Ошибка getUpdates:", e)

print("\n--- local processes ---")
try:
    if os.name == "nt":
        subprocess.run("tasklist | findstr python", shell=True)
    else:
        subprocess.run("ps aux | grep python", shell=True)
except Exception as e:
    print("Не удалось проверить процессы:", e)
