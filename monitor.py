import requests
import os
import sys
from datetime import datetime
import time
import random

print("=" * 60)
print("🚀 МОНИТОР АКТИВНОСТИ GTA5RP")
print("=" * 60)

# Получаем секреты из GitHub
BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')
URL = "https://forum.gta5rp.com/members/adminadminov.6/"

print(f"📋 Конфигурация:")
print(f"  • BOT_TOKEN: {'✅ Есть' if BOT_TOKEN else '❌ НЕТ'}")
print(f"  • CHAT_ID: {CHAT_ID}")
print(f"  • URL: {URL}")

# Проверка
if not BOT_TOKEN:
    print("\n❌ ОШИБКА: TELEGRAM_BOT_TOKEN не задан!")
    print("Добавьте в GitHub Secrets:")
    print("Name: TELEGRAM_BOT_TOKEN")
    print("Value: ваш_токен_от_BotFather")
    sys.exit(1)

if not CHAT_ID:
    print("\n❌ ОШИБКА: TELEGRAM_CHAT_ID не задан!")
    print("Добавьте в GitHub Secrets:")
    print("Name: TELEGRAM_CHAT_ID")
    print("Value: -1003600434530")
    sys.exit(1)

def check_page():
    """Проверяем страницу"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        print(f"\n🔍 Проверяем: {URL}")
        print(f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}")
        
        # Случайная задержка
        time.sleep(random.uniform(1, 3))
        
        response = requests.get(URL, headers=headers, timeout=10)
        
        if response.status_code == 200:
            html = response.text
            print(f"✅ Страница загружена ({len(html)} символов)")
            
            # Ищем "Только что"
            if "Только что" in html:
                print("\n🎯 НАЙДЕНО: 'Только что' на странице!")
                
                # Ищем контекст (активность)
                if "Активность:" in html:
                    print("✅ Найдена строка 'Активность:'")
                    return "Активность: Только что"
                else:
                    return "Только что (контекст не определен)"
            else:
                print("\nℹ️ Активности 'Только что' нет")
                return "Нет активности 'Только что'"
        else:
            print(f"\n❌ Ошибка загрузки: {response.status_code}")
            return f"Ошибка: {response.status_code}"
            
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        return f"Ошибка: {e}"

def send_telegram(message):
    """Отправляем сообщение в Telegram"""
    try:
        current_time = datetime.now().strftime('%d.%m.%Y %H:%M:%S')
        
        telegram_message = f"""
<b>🚨 ТЕСТОВЫЙ ЗАПУСК</b>

{message}

📅 Время: {current_time}
🔗 Ссылка: {URL}

✅ Монитор работает корректно!
При обнаружении 'Активность: Только что' 
придёт настоящее уведомление.
"""
        
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': CHAT_ID,
            'text': telegram_message,
            'parse_mode': 'HTML',
            'disable_web_page_preview': False
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            print("✅ Сообщение отправлено в Telegram!")
            return True
        else:
            print(f"❌ Ошибка отправки: {response.status_code}")
            print(f"Ответ: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка Telegram: {e}")
        return False

# Основная логика
if __name__ == "__main__":
    print("\n" + "=" * 60)
    
    # Проверяем страницу
    result = check_page()
    
    # Отправляем результат в Telegram
    print(f"\n📨 Отправляем результат в Telegram...")
    print(f"📊 Результат: {result}")
    
    success = send_telegram(f"Результат проверки: {result}")
    
    print("\n" + "=" * 60)
    if success:
        print("✅ ВСЁ ГОТОВО! Проверьте канал Telegram.")
    else:
        print("❌ Были ошибки. Проверьте логи выше.")
    
    print("Скрипт завершён.")
