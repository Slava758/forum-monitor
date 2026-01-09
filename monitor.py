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

def get_status_hash(status_text, active):
    """Создаём хеш статуса для сравнения"""
    status_string = f"{status_text}_{active}"
    return hashlib.md5(status_string.encode('utf-8')).hexdigest()

def analyze_page_structure(html):
    """Анализирует структуру страницы для поиска активности"""
    print(f"\n📐 Анализ структуры страницы:")
    
    # Ищем все "Активность" в любом регистре
    all_matches = list(re.finditer(r'Активность', html, re.IGNORECASE))
    
    if not all_matches:
        print("❌ Слово 'Активность' не найдено на странице!")
        
        # Ищем альтернативы
        alternatives = ['активность', 'АКТИВНОСТЬ', 'Active', 'active', 'онлайн', 'Online', 'последн', 'визит']
        for alt in alternatives:
            if alt in html.lower():
                print(f"✅ Найдено альтернативное: '{alt}'")
        
        # Покажем часть HTML где может быть информация
        print("\n🔍 Показываю часть HTML (первые 5000 символов):")
        print(html[:5000])
        return None
    
    print(f"✅ Найдено {len(all_matches)} вхождений 'Активность'")
    
    # Анализируем первые 5 вхождений
    for i, match in enumerate(all_matches[:5]):
        start = max(0, match.start() - 100)
        end = min(len(html), match.end() + 200)
        context = html[start:end]
        
        # Чистим HTML
        clean_context = re.sub('<[^<]+?>', ' ', context)
        clean_context = ' '.join(clean_context.split())
        
        print(f"\n--- Совпадение #{i+1} ---")
        print(f"Позиция в HTML: {match.start()}")
        print(f"Текст: '{clean_context[:300]}...'")
        
        # Проверяем есть ли "Вчера" или "Сегодня" или "Только что"
        if 'вчера' in clean_context.lower():
            print("📅 Содержит: 'Вчера'")
        if 'сегодня' in clean_context.lower():
            print("📅 Содержит: 'Сегодня'")
        if 'только что' in clean_context.lower():
            print("🎯 Содержит: 'Только что'")
    
    return all_matches

def find_current_status(html):
    """Находим текущий статус активности"""
    try:
        print(f"\n🔎 Поиск статуса активности...")
        
        # 1. Сначала ищем простым способом
        if "Активность" in html:
            # Ищем строку с активностью (200 символов после)
            lines = html.split('\n')
            for line in lines:
                if "Активность" in line:
                    # Убираем HTML теги
                    clean_line = re.sub('<[^<]+?>', ' ', line)
                    clean_line = ' '.join(clean_line.split())
                    
                    if len(clean_line) > 15 and "Активность" in clean_line:
                        print(f"✅ Найден в строке: '{clean_line[:150]}...'")
                        return clean_line
        
        # 2. Ищем по паттернам
        patterns = [
            r'Активность[^<]{10,150}',  # Активность + 10-150 символов
            r'активность[^<]{10,150}',  # маленькими
            r'Последняя активность[^<]{5,100}',
            r'был\(а\) на сайте[^<]{5,100}',
            r'Заходил\(а\)[^<]{5,100}',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            if matches:
                for match in matches:
                    clean = re.sub('<[^<]+?>', ' ', match).strip()
                    clean = ' '.join(clean.split())
                    if clean and len(clean) > 15:
                        print(f"✅ Найден паттерном: '{clean[:150]}...'")
                        return clean
        
        # 3. Если не нашли - анализируем структуру
        analyze_page_structure(html)
        
        # 4. Последняя попытка: ищем любую информацию о времени
        time_patterns = [
            r'\d{1,2}:\d{2}',  # время 12:34
            r'Вчера',
            r'Сегодня',
            r'Только что',
            r'\d+ \w+ \d{4}',  # 15 января 2024
        ]
        
        # Ищем блоки с временем
        for i in range(len(html) - 200):
            snippet = html[i:i+200]
            has_time = any(re.search(pattern, snippet) for pattern in time_patterns)
            has_activity = 'активн' in snippet.lower()
            
            if has_time and has_activity:
                clean_snippet = re.sub('<[^<]+?>', ' ', snippet).strip()
                clean_snippet = ' '.join(clean_snippet.split())
                if len(clean_snippet) > 20:
                    print(f"⏰ Найден временной блок: '{clean_snippet[:150]}...'")
                    return clean_snippet
        
        return "Активность: Не удалось определить"
        
    except Exception as e:
        print(f"❌ Ошибка поиска: {e}")
        return f"Активность: Ошибка"

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
            print(f"✅ Страница загружена ({len(html)} символов)")
            
            # Сохраняем HTML для отладки
            with open("debug_page.html", "w", encoding="utf-8") as f:
                f.write(html[:10000])
            print("💾 HTML сохранён в debug_page.html")
            
            # ============================================
            # ПОИСК "ТОЛЬКО ЧТО" (активность онлайн)
            # ============================================
            
            # Ищем "Только что" в любом регистре
            if re.search(r'Только что', html, re.IGNORECASE):
                print("🎯 Найдено 'Только что' на странице")
                
                # Ищем контекст с "Активность"
                pattern = r'Активность[^<]{0,50}Только что'
                match = re.search(pattern, html, re.IGNORECASE)
                
                if match:
                    found_text = match.group(0)
                    clean_text = re.sub('<[^<]+?>', ' ', found_text).strip()
                    clean_text = ' '.join(clean_text.split())
                    
                    print(f"✅ Найдена активность: '{clean_text}'")
                    
                    # Ищем местонахождение
                    location = find_location(html)
                    if location:
                        return {
                            'active': True,
                            'text': f"{clean_text}\n📍 {location}",
                            'location': location
                        }
                    else:
                        return {
                            'active': True,
                            'text': clean_text,
                            'location': None
                        }
                else:
                    # Если "Только что" есть, но не рядом с "Активность"
                    print("⚠️ 'Только что' найдено, но не рядом с 'Активность'")
            
            # ============================================
            # ЕСЛИ НЕ ОНЛАЙН - ПОЛУЧАЕМ ТЕКУЩИЙ СТАТУС
            # ============================================
            current_status = find_current_status(html)
            
            return {
                'active': False,
                'text': current_status,
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

def find_location(html):
    """Ищем где находится на форуме"""
    try:
        # Ищем после "Только что"
        lines = html.split('\n')
        
        for i, line in enumerate(lines):
            if "только что" in line.lower():
                # Смотрим следующие 3 строки
                for j in range(i+1, min(i+4, len(lines))):
                    next_line = lines[j].strip()
                    if next_line:
                        clean = re.sub('<[^<]+?>', ' ', next_line).strip()
                        clean = ' '.join(clean.split())
                        if clean and len(clean) > 5:
                            return clean[:200]
        
        return None
    except:
        return None

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
    print(f"📝 Предыдущий статус: {last_status['status_text'][:80] if last_status['status_text'] else 'Нет данных'}")
    
    # Проверяем текущую активность
    current_result = check_activity()
    
    # Создаём хеш
    current_hash = get_status_hash(current_result['text'], current_result['active'])
    
    print(f"\n📊 Текущая проверка:")
    print(f"  • Активен: {'✅ Да' if current_result['active'] else '❌ Нет'}")
    print(f"  • Статус: {current_result['text'][:100]}...")
    print(f"  • Хеш: {current_hash}")
    
    # Сравниваем с предыдущим
    status_changed = current_hash != last_status['status_hash']
    
    print(f"\n⚖️  Сравнение:")
    print(f"  • Статус изменился: {'✅ ДА' if status_changed else '❌ НЕТ'}")
    
    # Логика отправки
    send_message = False
    is_alert = False
    
    if status_changed:
        if current_result['active']:
            print("\n🚨 ОБНАРУЖЕНА НОВАЯ АКТИВНОСТЬ!")
            send_message = True
            is_alert = True
        else:
            print("\n📊 Статус изменился")
            send_message = True
            is_alert = False
    else:
        print("\nℹ️ Статус не изменился")
        
        # Первая проверка
        if not last_status['status_text']:
            print("📝 Первая проверка - отправляем")
            send_message = True
            is_alert = False
    
    # Отправляем если нужно
    if send_message:
        print(f"\n📨 Отправляем в Telegram...")
        success = send_telegram_message(current_result['text'], is_alert=is_alert)
        
        if success:
            print("✅ Сообщение отправлено!")
        else:
            print("❌ Не удалось отправить")
    else:
        print("\n📭 Сообщение НЕ отправляется")
    
    # Сохраняем статус
    save_status(current_result['text'], current_result['active'], current_hash)
    
    print("\n" + "=" * 60)
    print("✅ Проверка завершена")

if __name__ == "__main__":
    main()
