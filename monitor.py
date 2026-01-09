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
STATUS_FILE = "last_status.json"

print(f"🔧 Конфигурация:")
print(f"  • BOT_TOKEN: {'✅ Есть' if BOT_TOKEN else '❌ НЕТ'}")
print(f"  • CHAT_ID: {CHAT_ID}")
print(f"  • URL: {URL}")

if not BOT_TOKEN or not CHAT_ID:
    print("\n❌ ОШИБКА: Не заданы токен или chat_id!")
    sys.exit(1)

def load_last_status():
    """Загружаем последний сохранённый статус"""
    try:
        with open(STATUS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
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

def normalize_status(status_text):
    """Нормализуем текст статуса для сравнения (убираем лишнее)"""
    if not status_text:
        return ""
    
    # Приводим к нижнему регистру
    normalized = status_text.lower()
    
    # Заменяем множественные пробелы на один
    normalized = ' '.join(normalized.split())
    
    # Убираем спецсимволы которые могут меняться
    normalized = re.sub(r'[^\w\s:а-яА-ЯёЁ0-9\-]', ' ', normalized)
    
    # Нормализуем время (14:30 и 14.30 -> одинаково)
    normalized = re.sub(r'(\d{1,2})[.:](\d{2})', r'\1:\2', normalized)
    
    # Убираем лишние слова которые не важны для сравнения
    remove_words = ['📍', 'активность:', 'активность', 'не удалось определить', 'ошибка', 'статус:']
    for word in remove_words:
        normalized = normalized.replace(word, '')
    
    # Убираем лишние пробелы
    normalized = ' '.join(normalized.split())
    
    print(f"   Нормализовано: '{status_text[:50]}...' -> '{normalized[:50]}...'")
    return normalized.strip()

def get_status_hash(status_text, active):
    """Создаём хеш статуса для сравнения (с нормализацией)"""
    # Нормализуем текст перед созданием хеша
    normalized_text = normalize_status(status_text)
    status_string = f"{normalized_text}_{active}"
    hash_result = hashlib.md5(status_string.encode('utf-8')).hexdigest()
    
    print(f"   Хеш создан: '{status_string[:50]}...' -> {hash_result[:8]}...")
    return hash_result

def extract_activity_from_html(html):
    """Извлекаем информацию об активности"""
    print(f"\n🎯 Ищем блок активности...")
    
    try:
        # СПОСОБ 1: Ищем пары dt/dd (самый надёжный для XenForo)
        dt_matches = list(re.finditer(r'<dt[^>]*>(.*?)</dt>', html, re.IGNORECASE | re.DOTALL))
        dd_matches = list(re.finditer(r'<dd[^>]*>(.*?)</dd>', html, re.IGNORECASE | re.DOTALL))
        
        if dt_matches and dd_matches:
            # Ищем пару где <dt> содержит "Активность"
            for i, dt_match in enumerate(dt_matches):
                dt_text = re.sub('<[^<]+?>', '', dt_match.group(1)).strip()
                
                if 'активность' in dt_text.lower():
                    # Берём соответствующий <dd>
                    if i < len(dd_matches):
                        dd_text = re.sub('<[^<]+?>', '', dd_matches[i].group(1)).strip()
                        result = f"{dt_text}: {dd_text}"
                        return result
        
        # СПОСОБ 2: Ищем текст после "Регистрация"
        reg_pattern = r'Регистрация[^<]{10,150}'
        reg_match = re.search(reg_pattern, html, re.IGNORECASE)
        
        if reg_match:
            reg_end = reg_match.end()
            # Берём текст после регистрации (500 символов)
            after_reg = html[reg_end:reg_end + 500]
            
            # Ищем в этом тексте "Активность"
            activity_pattern = r'Активность[^<]{10,150}'
            activity_match = re.search(activity_pattern, after_reg, re.IGNORECASE)
            
            if activity_match:
                activity_text = activity_match.group(0)
                clean_activity = re.sub('<[^<]+?>', ' ', activity_text).strip()
                clean_activity = ' '.join(clean_activity.split())
                return clean_activity
        
        # СПОСОБ 3: Простой поиск по строкам
        lines = html.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            if 'активность' in line_lower and ('вчера' in line_lower or 'сегодня' in line_lower or 'только что' in line_lower):
                clean_line = re.sub('<[^<]+?>', ' ', line).strip()
                clean_line = ' '.join(clean_line.split())
                return clean_line
        
        return "Активность не определена"
        
    except Exception as e:
        print(f"❌ Ошибка извлечения: {e}")
        return f"Ошибка: {str(e)[:50]}"

def check_activity():
    """Проверяем активность"""
    print(f"\n🔍 Проверяем: {URL}")
    print(f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(URL, headers=headers, timeout=10)
        
        if response.status_code == 200:
            html = response.text
            
            # Извлекаем информацию об активности
            activity_text = extract_activity_from_html(html)
            print(f"\n📊 Извлечённая активность: '{activity_text}'")
            
            # Проверяем если "Только что"
            if activity_text and 'только что' in activity_text.lower():
                print("🎯 ОБНАРУЖЕНА АКТИВНОСТЬ 'ТОЛЬКО ЧТО'!")
                return {
                    'active': True,
                    'text': activity_text,
                    'location': None
                }
            
            # Если не онлайн
            return {
                'active': False,
                'text': activity_text if activity_text else "Активность не найдена",
                'location': None
            }
            
        else:
            error_msg = f"❌ Ошибка загрузки: {response.status_code}"
            print(error_msg)
            return {
                'active': False,
                'text': error_msg,
                'location': None
            }
            
    except Exception as e:
        error_msg = f"❌ Ошибка: {str(e)[:100]}"
        print(error_msg)
        return {
            'active': False,
            'text': error_msg,
            'location': None
        }

def send_telegram_message(message, is_alert=False):
    """Отправляем сообщение в Telegram"""
    try:
        current_time = datetime.now().strftime('%d.%m.%Y %H:%M:%S')
        
        if is_alert:
            telegram_msg = f"""
<b>🚨 АКТИВНОСТЬ ОБНАРУЖЕНА!</b>

📅 <b>Время:</b> {current_time}
🔗 <b>Ссылка:</b> <a href="{URL}">{URL}</a>

📊 <b>Статус:</b>
<code>{message}</code>

🎯 <b>Пользователь в сети!</b>
"""
        else:
            telegram_msg = f"""
<b>📊 Статус изменился</b>

📅 <b>Время:</b> {current_time}
🔗 <b>Ссылка:</b> <a href="{URL}">{URL}</a>

📝 <b>Новый статус:</b>
<code>{message}</code>
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
    """Основная логика"""
    print("\n" + "=" * 60)
    
    # Загружаем предыдущий статус
    last_status = load_last_status()
    last_status_text = last_status.get('status_text', '')
    print(f"📝 Предыдущий статус: {last_status_text[:80] if last_status_text else 'Нет данных'}")
    print(f"   Последняя проверка: {last_status.get('last_check', 'Никогда')}")
    print(f"   Был активен: {'✅ Да' if last_status.get('active', False) else '❌ Нет'}")
    print(f"   Хеш: {last_status.get('status_hash', '')[:12]}...")
    
    # Проверяем текущую активность
    current_result = check_activity()
    
    # Создаём хеш ТЕКУЩЕГО статуса (с нормализацией)
    current_hash = get_status_hash(current_result['text'], current_result['active'])
    
    print(f"\n📊 Текущая проверка:")
    print(f"  • Активен: {'✅ Да' if current_result['active'] else '❌ Нет'}")
    print(f"  • Статус: {current_result['text'][:100]}...")
    print(f"  • Хеш: {current_hash[:12]}...")
    
    # Сравниваем с предыдущим
    status_changed = current_hash != last_status.get('status_hash', '')
    
    print(f"\n⚖️  Сравнение:")
    print(f"  • Статус изменился: {'✅ ДА' if status_changed else '❌ НЕТ'}")
    print(f"  • Предыдущий хеш: {last_status.get('status_hash', '')[:12]}...")
    print(f"  • Текущий хеш: {current_hash[:12]}...")
    
    # Логика отправки
    send_message = False
    is_alert = False
    
    if status_changed:
        if current_result['active']:
            print("\n🚨 ОБНАРУЖЕНА НОВАЯ АКТИВНОСТЬ 'ТОЛЬКО ЧТО'!")
            send_message = True
            is_alert = True
        else:
            print("\n📊 Статус изменился (не активность)")
            send_message = True
            is_alert = False
    else:
        print("\nℹ️ Статус НЕ изменился (всё то же самое)")
        
        # Первая проверка (пустая история)
        if not last_status_text:
            print("📝 Первая проверка - отправляем приветствие")
            send_message = True
            is_alert = False
    
    # Отправляем если нужно
    if send_message:
        print(f"\n📨 Отправляем в Telegram ({'АЛЕРТ' if is_alert else 'СТАТУС'})...")
        success = send_telegram_message(current_result['text'], is_alert=is_alert)
        
        if success:
            print("✅ Сообщение отправлено!")
        else:
            print("❌ Не удалось отправить")
    else:
        print("\n📭 Сообщение НЕ отправляется (статус не изменился)")
    
    # Сохраняем статус
    save_status(current_result['text'], current_result['active'], current_hash)
    
    print("\n" + "=" * 60)
    print("✅ Проверка завершена")

if __name__ == "__main__":
    main()
