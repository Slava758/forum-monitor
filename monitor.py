import requests
import os
import sys
from datetime import datetime
import re
import json
import hashlib

print("=" * 60)
print("🚀 МОНИТОР АКТИВНОСТИ GTA5RP")
print("=" * 60)

# Конфигурация
BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')
URL = "https://forum.gta5rp.com/members/adminadminov.6/"
STATUS_FILE = "last_status.json"  # Файл для хранения последнего статуса

print(f"🔧 Конфигурация:")
print(f"  • BOT_TOKEN: {'✅ Есть' if BOT_TOKEN else '❌ НЕТ'}")
print(f"  • CHAT_ID: {CHAT_ID}")
print(f"  • URL: {URL}")

# Проверяем настройки
if not BOT_TOKEN or not CHAT_ID:
    print("\n❌ ОШИБКА: Не заданы токен или chat_id!")
    sys.exit(1)

def load_last_status():
    """Загружаем последний сохранённый статус"""
    try:
        with open(STATUS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        # Если файла нет, возвращаем пустой статус
        return {
            'status_text': '',
            'status_hash': '',
            'last_check': '',
            'active': False
        }

def save_status(status_text, active, status_hash):
    """Сохраняем текущий статус"""
    status_data = {
        'status_text': status_text,
        'status_hash': status_hash,
        'last_check': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'active': active
    }
    
    with open(STATUS_FILE, 'w', encoding='utf-8') as f:
        json.dump(status_data, f, ensure_ascii=False, indent=2)
    
    print(f"💾 Сохранён статус: {status_text[:50]}...")

def get_status_hash(status_text, active):
    """Создаём хеш статуса для сравнения"""
    status_string = f"{status_text}_{active}"
    return hashlib.md5(status_string.encode('utf-8')).hexdigest()

def check_activity():
    """Проверяем активность - БЕЗ ДВОЕТОЧИЯ"""
    print(f"\n🔍 Проверяем: {URL}")
    print(f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(URL, headers=headers, timeout=10)
        
        if response.status_code == 200:
            html = response.text
            
            print(f"✅ Страница загружена ({len(html)} символов)")
            
            # ============================================
            # ПРОВЕРКА АКТИВНОСТИ "ТОЛЬКО ЧТО"
            # ============================================
            
            # Паттерны для поиска активности "Только что" - БЕЗ двоеточия!
            patterns = [
                r'Активность\s+Только что',       # с пробелом
                r'Активность\s+только что',       # маленькие буквы
                r'Активность\s*Только что',       # возможны разные пробелы
                r'активность\s+только что',       # все маленькие
                r'АктивностьТолько что',          # слитно
            ]
            
            for pattern in patterns:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    found_text = match.group(0)
                    print(f"🎯 АКТИВНОСТЬ ОБНАРУЖЕНА: '{found_text}'")
                    
                    # Ищем что делает на форуме
                    location = find_location(html)
                    
                    status_text = found_text
                    if location:
                        status_text = f"{found_text}\n📍 {location}"
                    
                    return {
                        'active': True,
                        'text': status_text,
                        'location': location,
                        'type': 'activity_found'
                    }
            
            # ============================================
            # ЕСЛИ НЕ АКТИВЕН - ПОЛУЧАЕМ ТЕКУЩИЙ СТАТУС
            # ============================================
            current_status = find_current_status(html)
            print(f"📊 Текущий статус: {current_status}")
            
            return {
                'active': False,
                'text': current_status,
                'location': None,
                'type': 'status_update'
            }
            
        else:
            error_msg = f"❌ Ошибка загрузки: {response.status_code}"
            print(error_msg)
            return {
                'active': False,
                'text': error_msg,
                'location': None,
                'type': 'error'
            }
            
    except Exception as e:
        error_msg = f"❌ Ошибка: {str(e)[:100]}"
        print(error_msg)
        return {
            'active': False,
            'text': error_msg,
            'location': None,
            'type': 'error'
        }

def find_location(html):
    """Ищем где находится на форуме"""
    try:
        # Ищем текст после "Только что"
        lines = html.split('\n')
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if "только что" in line_lower:
                # Смотрим следующие 2 строки
                for j in range(i+1, min(i+3, len(lines))):
                    next_line = lines[j].strip()
                    if not next_line:
                        continue
                    
                    # Убираем HTML теги
                    clean_line = re.sub('<[^<]+?>', '', next_line).strip()
                    
                    # Проверяем что это не техническая информация
                    if (clean_line and len(clean_line) > 3 and 
                        not clean_line.startswith(('{', '[', '<', 'http', '//'))):
                        return clean_line[:150]
        
        return None
        
    except:
        return None

def find_current_status(html):
    """Находим текущий статус активности - БЕЗ ДВОЕТОЧИЯ"""
    try:
        # Ищем БЕЗ двоеточия
        patterns = [
            r'Активность\s+Вчера[^<]*',      # Активность Вчера в ...
            r'Активность\s+Сегодня[^<]*',    # Активность Сегодня в ...
            r'Активность\s+\d+[^<]*',        # Активность [число] ...
            r'Активность\s+[^<]{5,100}',     # Активность что-то
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                status = match.group(0)
                clean_status = re.sub('<[^<]+?>', '', status).strip()
                clean_status = ' '.join(clean_status.split())
                
                if clean_status and len(clean_status) > len("Активность") + 3:
                    return clean_status
        
        # Если не нашли, возвращаем общее
        return "Активность не определена"
        
    except:
        return "Активность (ошибка определения)"

def send_telegram_message(message, is_alert=False):
    """Отправляем сообщение в Telegram"""
    try:
        current_time = datetime.now().strftime('%d.%m.%Y %H:%M:%S')
        
        if is_alert:
            # УВЕДОМЛЕНИЕ ОБ АКТИВНОСТИ
            telegram_msg = f"""
<b>🚨 АКТИВНОСТЬ ОБНАРУЖЕНА!</b>

📅 <b>Время:</b> {current_time}
🔗 <b>Ссылка:</b> <a href="{URL}">{URL}</a>

📊 <b>Статус:</b>
<code>{message}</code>

🎯 <b>Пользователь в сети!</b>

#мониторинг #активность
"""
        else:
            # ОБЫЧНОЕ УВЕДОМЛЕНИЕ О ИЗМЕНЕНИИ
            telegram_msg = f"""
<b>📊 Статус изменился</b>

📅 <b>Время:</b> {current_time}
🔗 <b>Ссылка:</b> <a href="{URL}">{URL}</a>

📝 <b>Новый статус:</b>
<code>{message}</code>

#мониторинг #статус
"""
        
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': CHAT_ID,
            'text': telegram_msg,
            'parse_mode': 'HTML',
            'disable_web_page_preview': False
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ Сообщение отправлено!")
            return True
        else:
            print(f"❌ Ошибка отправки: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка Telegram: {e}")
        return False

def main():
    """Основная логика с отслеживанием изменений"""
    print("\n" + "=" * 60)
    
    # Загружаем предыдущий статус
    last_status = load_last_status()
    print(f"📝 Предыдущий статус: {last_status['status_text'][:80] if last_status['status_text'] else 'Нет данных'}")
    print(f"   Последняя проверка: {last_status['last_check']}")
    print(f"   Был активен: {'✅ Да' if last_status['active'] else '❌ Нет'}")
    
    # Проверяем текущую активность
    current_result = check_activity()
    
    # Создаём хеш текущего статуса
    current_hash = get_status_hash(current_result['text'], current_result['active'])
    
    print(f"\n📊 Текущая проверка:")
    print(f"  • Активен: {'✅ Да' if current_result['active'] else '❌ Нет'}")
    print(f"  • Статус: {current_result['text'][:100]}...")
    print(f"  • Хеш статуса: {current_hash}")
    
    # Сравниваем с предыдущим статусом
    status_changed = current_hash != last_status['status_hash']
    
    print(f"\n⚖️  Сравнение:")
    print(f"  • Статус изменился: {'✅ ДА' if status_changed else '❌ НЕТ'}")
    print(f"  • Предыдущий хеш: {last_status['status_hash']}")
    print(f"  • Текущий хеш: {current_hash}")
    
    # ============================================
    # ЛОГИКА ОТПРАВКИ СООБЩЕНИЙ
    # ============================================
    
    send_message = False
    message_type = "status_change"  # или "activity_alert"
    
    if status_changed:
        # Статус изменился
        if current_result['active']:
            # Обнаружена активность "Только что"
            print("\n🚨 ОБНАРУЖЕНА НОВАЯ АКТИВНОСТЬ!")
            send_message = True
            message_type = "activity_alert"
        else:
            # Изменился обычный статус (Вчера/Сегодня/другое)
            print("\n📊 Статус изменился (не активность)")
            send_message = True
            message_type = "status_change"
    else:
        # Статус не изменился
        print("\nℹ️ Статус не изменился")
        
        # Если это первая проверка (нет предыдущего статуса)
        if not last_status['status_text']:
            print("📝 Первая проверка - отправляем приветственное сообщение")
            send_message = True
            message_type = "first_check"
    
    # Отправляем сообщение если нужно
    if send_message:
        print(f"\n📨 Отправляем сообщение в Telegram...")
        
        if message_type == "activity_alert":
            success = send_telegram_message(current_result['text'], is_alert=True)
        else:
            success = send_telegram_message(current_result['text'], is_alert=False)
        
        if success:
            print("✅ Сообщение отправлено!")
        else:
            print("❌ Не удалось отправить сообщение")
    else:
        print("\n📭 Сообщение НЕ отправляется (статус не изменился)")
    
    # Сохраняем текущий статус
    save_status(current_result['text'], current_result['active'], current_hash)
    
    print("\n" + "=" * 60)
    print("✅ Проверка завершена")

if __name__ == "__main__":
    main()
