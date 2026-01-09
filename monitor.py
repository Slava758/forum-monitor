import requests
import os
import sys
from datetime import datetime
import re
import json

print("=" * 60)
print("🚀 МОНИТОР АКТИВНОСТИ GTA5RP")
print("=" * 60)

# Конфигурация
BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')
URL = "https://forum.gta5rp.com/members/adminadminov.6/"
STATUS_FILE = "last_time_status.txt"

print(f"🔧 Конфигурация:")
print(f"  • BOT_TOKEN: {'✅ Есть' if BOT_TOKEN else '❌ НЕТ'}")
print(f"  • CHAT_ID: {CHAT_ID}")
print(f"  • URL: {URL}")

if not BOT_TOKEN or not CHAT_ID:
    print("\n❌ ОШИБКА: Не заданы токен или chat_id!")
    sys.exit(1)

def extract_time_content(html):
    """Извлекаем текст из ВСЕХ <time> тегов и находим нужный"""
    print(f"\n🔍 Ищем текст в <time> тегах...")
    
    try:
        # Находим ВСЕ <time> теги
        time_tags = re.findall(r'<time[^>]*>(.*?)</time>', html, re.IGNORECASE)
        
        if not time_tags:
            print("❌ Не найдено ни одного <time> тега")
            return None
        
        print(f"✅ Найдено {len(time_tags)} <time> тегов:")
        
        # Ищем тег который содержит время активности
        for i, content in enumerate(time_tags):
            content = content.strip()
            print(f"  [{i}] '{content}'")
            
            # Это может быть: "Вчера в 15:55", "Только что", "2 часа назад" и т.д.
            # Проверяем что это похоже на время активности
            time_patterns = [
                r'Только что',
                r'\d+ \w+ назад',  # "2 часа назад", "5 минут назад"
                r'Вчера в \d{1,2}:\d{2}',
                r'Сегодня в \d{1,2}:\d{2}',
                r'\d{1,2}:\d{2}',  # Просто время
            ]
            
            for pattern in time_patterns:
                if re.search(pattern, content):
                    print(f"🎯 Найден подходящий <time> тег: '{content}'")
                    return content
        
        print("⚠️ Не найден <time> тег с временем активности")
        
        # Попробуем найти по контексту (рядом со словом "Активность")
        activity_index = html.find('Активность')
        if activity_index != -1:
            # Берём кусок HTML вокруг "Активность"
            context = html[max(0, activity_index - 200):min(len(html), activity_index + 200)]
            
            # Ищем <time> в этом контексте
            time_match = re.search(r'<time[^>]*>(.*?)</time>', context, re.IGNORECASE)
            if time_match:
                content = time_match.group(1).strip()
                print(f"🎯 Найден <time> тег рядом с 'Активность': '{content}'")
                return content
        
        return None
        
    except Exception as e:
        print(f"❌ Ошибка извлечения: {e}")
        return None

def load_last_time_status():
    """Загружаем последний статус времени"""
    try:
        with open(STATUS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"📝 Предыдущий статус времени: '{data.get('time_text', 'Нет')}'")
            return data
    except:
        print("📝 Предыдущий статус времени: Нет данных")
        return {
            'time_text': '',
            'timestamp': ''
        }

def save_time_status(time_text):
    """Сохраняем текущий статус времени"""
    data = {
        'time_text': time_text,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    with open(STATUS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"💾 Сохранён статус времени: '{time_text}'")

def check_page():
    """Проверяем страницу и извлекаем время"""
    print(f"\n🔍 Проверяем: {URL}")
    print(f"⏰ Время проверки: {datetime.now().strftime('%H:%M:%S')}")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(URL, headers=headers, timeout=10)
        
        if response.status_code == 200:
            html = response.text
            
            # Извлекаем текст из <time> тега
            time_content = extract_time_content(html)
            
            if time_content:
                # Проверяем если "Только что"
                is_online = 'только что' in time_content.lower()
                
                return {
                    'time_text': time_content,
                    'is_online': is_online,
                    'status': 'found'
                }
            else:
                return {
                    'time_text': 'Не удалось найти время',
                    'is_online': False,
                    'status': 'not_found'
                }
        else:
            return {
                'time_text': f'Ошибка: {response.status_code}',
                'is_online': False,
                'status': 'error'
            }
            
    except Exception as e:
        return {
            'time_text': f'Ошибка: {str(e)[:50]}',
            'is_online': False,
            'status': 'error'
        }

def send_telegram_alert(time_text):
    """Отправляем уведомление в Telegram при активности"""
    try:
        current_time = datetime.now().strftime('%d.%m.%Y %H:%M:%S')
        
        message = f"""
<b>🚨 ПОЛЬЗОВАТЕЛЬ В СЕТИ!</b>

📅 <b>Обнаружено:</b> {current_time}
🔗 <b>Ссылка:</b> <a href="{URL}">{URL}</a>

⏰ <b>Активность:</b>
<code>Активность: {time_text}</code>

🎯 <b>Статус: онлайн</b>
"""
        
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': CHAT_ID,
            'text': message,
            'parse_mode': 'HTML',
            'disable_web_page_preview': False
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ Уведомление отправлено!")
            return True
        else:
            print(f"❌ Ошибка отправки: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка Telegram: {e}")
        return False

def main():
    """Основная логика - отправляем ТОЛЬКО при "Только что" """
    print("\n" + "=" * 60)
    
    # Загружаем предыдущий статус
    last_status = load_last_time_status()
    last_time_text = last_status.get('time_text', '')
    
    # Проверяем текущую страницу
    current_result = check_page()
    current_time_text = current_result.get('time_text', '')
    current_is_online = current_result.get('is_online', False)
    
    print(f"\n📊 Сравнение:")
    print(f"  • Было: '{last_time_text}'")
    print(f"  • Стало: '{current_time_text}'")
    print(f"  • Онлайн сейчас: {'✅ ДА' if current_is_online else '❌ НЕТ'}")
    
    # ============================================
    # ПРОСТАЯ ЛОГИКА: отправляем ТОЛЬКО если:
    # 1. Текст В <time> теге = "Только что"
    # 2. И это ИЗМЕНИЛОСЬ по сравнению с прошлым разом
    # ============================================
    
    send_alert = False
    
    # Условие 1: Сейчас "Только что"
    if current_is_online:
        print(f"\n🎯 Обнаружено: '{current_time_text}' (онлайн!)")
        
        # Условие 2: Это ИЗМЕНЕНИЕ (раньше было не "Только что")
        if last_time_text and 'только что' not in last_time_text.lower():
            print(f"✅ ИЗМЕНЕНИЕ! Было: '{last_time_text}' → Стало: '{current_time_text}'")
            send_alert = True
        elif not last_time_text:
            # Первая проверка
            print(f"✅ Первая проверка, пользователь онлайн")
            send_alert = True
        else:
            print(f"ℹ️ Пользователь уже был онлайн в прошлой проверке")
    else:
        print(f"\nℹ️ Пользователь не онлайн: '{current_time_text}'")
    
    # Отправляем уведомление если нужно
    if send_alert:
        print(f"\n📨 Отправляем уведомление об активности...")
        success = send_telegram_alert(current_time_text)
        
        if success:
            print("✅ Уведомление отправлено!")
        else:
            print("❌ Не удалось отправить")
    else:
        print(f"\n📭 Уведомление НЕ отправляется")
    
    # Сохраняем текущий статус
    save_time_status(current_time_text)
    
    print("\n" + "=" * 60)
    print("✅ Проверка завершена")

if __name__ == "__main__":
    main()
