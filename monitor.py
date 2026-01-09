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
    
    print(f"💾 Сохранён статус: '{status_text[:50]}...'")

def extract_pure_activity_text(html):
    """Извлекаем ЧИСТЫЙ текст активности (без HTML, без лишнего)"""
    print(f"\n🎯 Извлекаем чистый текст активности...")
    
    try:
        # 1. Убираем все скрипты и стили
        html_clean = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html_clean = re.sub(r'<style[^>]*>.*?</style>', '', html_clean, flags=re.DOTALL | re.IGNORECASE)
        
        # 2. Заменяем HTML теги на пробелы
        html_clean = re.sub(r'<[^>]+>', ' ', html_clean)
        
        # 3. Заменяем множественные пробелы и переносы на один пробел
        html_clean = re.sub(r'\s+', ' ', html_clean)
        
        # 4. Ищем паттерн активности в очищенном тексте
        # Паттерн: "Активность" + что-то + время
        patterns = [
            r'Активность[^:]{0,5}:[^0-9]{0,20}(\d{1,2}[:.]\d{2})',  # с двоеточием и временем
            r'Активность[^0-9]{0,20}(\d{1,2}[:.]\d{2})',           # без двоеточия, с временем
            r'Активность[^А-Яа-я0-9]{0,10}(Вчера|Сегодня|Только что)',  # с Вчера/Сегодня/Только что
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html_clean, re.IGNORECASE)
            if matches:
                # Находим полное совпадение
                full_match = re.search(pattern, html_clean, re.IGNORECASE)
                if full_match:
                    activity_text = full_match.group(0).strip()
                    print(f"✅ Найдена активность: '{activity_text}'")
                    
                    # Нормализуем текст
                    normalized = activity_text
                    normalized = re.sub(r'\s+', ' ', normalized)  # Убираем лишние пробелы
                    normalized = normalized.replace('  ', ' ')
                    
                    # Если есть время, нормализуем формат
                    normalized = re.sub(r'(\d{1,2})[.:](\d{2})', r'\1:\2', normalized)
                    
                    return normalized
        
        # 5. Если не нашли по паттернам, ищем вручную
        print("🔍 Ручной поиск активности в тексте...")
        
        # Разбиваем на предложения
        sentences = re.split(r'[.!?]', html_clean)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if 'активность' in sentence.lower() and len(sentence) < 200:
                # Проверяем что это действительно статус активности
                has_time = bool(re.search(r'\d{1,2}[:.]\d{2}', sentence))
                has_day = any(word in sentence.lower() for word in ['вчера', 'сегодня', 'только что'])
                
                if has_time or has_day:
                    print(f"✅ Найдена в предложении: '{sentence}'")
                    
                    # Нормализуем
                    normalized = sentence.strip()
                    normalized = re.sub(r'\s+', ' ', normalized)
                    normalized = re.sub(r'(\d{1,2})[.:](\d{2})', r'\1:\2', normalized)
                    
                    return normalized
        
        print("❌ Активность не найдена")
        return "Активность не определена"
        
    except Exception as e:
        print(f"❌ Ошибка извлечения: {e}")
        return f"Ошибка: {str(e)[:50]}"

def normalize_for_comparison(text):
    """Нормализуем текст для сравнения (максимально агрессивно)"""
    if not text:
        return ""
    
    # Приводим к нижнему регистру
    normalized = text.lower()
    
    # Убираем ВСЕ не-буквы и не-цифры (кроме : и пробела)
    normalized = re.sub(r'[^\w\s:]', ' ', normalized)
    
    # Заменяем все пробельные символы на один пробел
    normalized = re.sub(r'\s+', ' ', normalized)
    
    # Нормализуем время
    normalized = re.sub(r'(\d{1,2})[.:](\d{2})', r'\1:\2', normalized)
    
    # Убираем слова которые не важны
    remove_words = ['активность', 'activity', 'статус', 'status', 'не', 'удалось', 'определить', 'ошибка', 'error']
    for word in remove_words:
        normalized = normalized.replace(word, '')
    
    # Убираем лишние пробелы
    normalized = normalized.strip()
    
    return normalized

def get_status_hash(status_text, active):
    """Создаём хеш статуса для сравнения"""
    # Нормализуем ДЛЯ СРАВНЕНИЯ
    normalized = normalize_for_comparison(status_text)
    status_string = f"{normalized}_{active}"
    
    print(f"   Для сравнения: '{status_text[:50]}...'")
    print(f"   Нормализовано: '{normalized[:50]}...'")
    
    return hashlib.md5(status_string.encode('utf-8')).hexdigest()

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
            
            # Извлекаем ЧИСТЫЙ текст активности
            activity_text = extract_pure_activity_text(html)
            print(f"\n📊 Извлечённая активность: '{activity_text}'")
            
            # Проверяем если "Только что"
            if 'только что' in activity_text.lower():
                print("🎯 ОБНАРУЖЕНА АКТИВНОСТЬ 'ТОЛЬКО ЧТО'!")
                return {
                    'active': True,
                    'text': activity_text
                }
            
            # Если не онлайн
            return {
                'active': False,
                'text': activity_text
            }
            
        else:
            error_msg = f"❌ Ошибка загрузки: {response.status_code}"
            print(error_msg)
            return {
                'active': False,
                'text': error_msg
            }
            
    except Exception as e:
        error_msg = f"❌ Ошибка: {str(e)[:100]}"
        print(error_msg)
        return {
            'active': False,
            'text': error_msg
        }

def send_telegram_message(message, is_alert=False, force_send=False):
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
        elif force_send:
            telegram_msg = f"""
<b>🔄 Первый запуск монитора</b>

📅 <b>Время:</b> {current_time}
🔗 <b>Ссылка:</b> <a href="{URL}">{URL}</a>

📊 <b>Текущий статус:</b>
<code>{message}</code>

✅ Монитор запущен и работает.
Уведомления будут приходить только при изменениях.
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
    last_hash = last_status.get('status_hash', '')
    
    print(f"📝 Предыдущий статус: '{last_status_text[:80]}...'")
    print(f"   Хеш: {last_hash[:16] if last_hash else 'Нет'}...")
    print(f"   Активен был: {'✅ Да' if last_status.get('active', False) else '❌ Нет'}")
    
    # Проверяем текущую активность
    current_result = check_activity()
    
    # Создаём хеш ТЕКУЩЕГО статуса
    current_hash = get_status_hash(current_result['text'], current_result['active'])
    
    print(f"\n📊 Текущая проверка:")
    print(f"  • Активен: {'✅ Да' if current_result['active'] else '❌ Нет'}")
    print(f"  • Статус: '{current_result['text'][:100]}...'")
    print(f"  • Хеш: {current_hash[:16]}...")
    
    # Сравниваем с предыдущим
    status_changed = current_hash != last_hash
    
    print(f"\n⚖️  Сравнение хешей:")
    print(f"  • Предыдущий: {last_hash[:16] if last_hash else 'Нет'}...")
    print(f"  • Текущий:    {current_hash[:16]}...")
    print(f"  • Изменился:  {'✅ ДА' if status_changed else '❌ НЕТ'}")
    
    # ============================================
    # НОВАЯ ЛОГИКА: ОТПРАВЛЯЕМ ТОЛЬКО ПРИ РЕАЛЬНЫХ ИЗМЕНЕНИЯХ
    # ============================================
    
    send_message = False
    is_alert = False
    force_send = False
    
    if not last_hash:
        # ПЕРВЫЙ ЗАПУСК - отправляем приветствие
        print("\n📝 Это первая проверка")
        send_message = True
        force_send = True
    
    elif status_changed:
        # Статус ИЗМЕНИЛСЯ по хешу
        if current_result['active']:
            print("\n🚨 ОБНАРУЖЕНА НОВАЯ АКТИВНОСТЬ 'ТОЛЬКО ЧТО'!")
            send_message = True
            is_alert = True
        else:
            # Проверяем ЧТО именно изменилось
            print("\n🔍 Анализируем изменение статуса...")
            
            # Извлекаем время из текущего и предыдущего статуса
            current_time_match = re.search(r'(\d{1,2}:\d{2})', current_result['text'])
            last_time_match = re.search(r'(\d{1,2}:\d{2})', last_status_text)
            
            current_day_match = re.search(r'(Вчера|Сегодня|Только что)', current_result['text'], re.IGNORECASE)
            last_day_match = re.search(r'(Вчера|Сегодня|Только что)', last_status_text, re.IGNORECASE)
            
            current_time = current_time_match.group(1) if current_time_match else None
            last_time = last_time_match.group(1) if last_time_match else None
            current_day = current_day_match.group(1) if current_day_match else None
            last_day = last_day_match.group(1) if last_day_match else None
            
            print(f"   Сравнение деталей:")
            print(f"   • Было: день='{last_day}', время='{last_time}'")
            print(f"   • Стало: день='{current_day}', время='{current_time}'")
            
            # Отправляем только если изменился день ИЛИ время
            if (current_day and last_day and current_day.lower() != last_day.lower()) or \
               (current_time and last_time and current_time != last_time):
                print("📊 Статус РЕАЛЬНО изменился (день или время)")
                send_message = True
                is_alert = False
            else:
                print("ℹ️ Статус технически изменился, но не существенно")
                send_message = False
    else:
        print("\n✅ Статус НЕ изменился (всё то же самое)")
    
    # Отправляем если нужно
    if send_message:
        print(f"\n📨 Отправляем сообщение...")
        success = send_telegram_message(
            current_result['text'], 
            is_alert=is_alert, 
            force_send=force_send
        )
        
        if success:
            print("✅ Сообщение отправлено!")
        else:
            print("❌ Не удалось отправить")
    else:
        print("\n📭 Сообщение НЕ отправляется (нет значимых изменений)")
    
    # Всегда сохраняем статус
    save_status(current_result['text'], current_result['active'], current_hash)
    
    print("\n" + "=" * 60)
    print("✅ Проверка завершена")

if __name__ == "__main__":
    main()
