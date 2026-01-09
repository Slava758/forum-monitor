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

def extract_activity_from_html(html):
    """Извлекаем информацию об активности ИЗ ПРАВИЛЬНОГО МЕСТА"""
    print(f"\n🎯 Ищем блок активности...")
    
    try:
        # ============================================
        # СПОСОБ 1: Ищем по структуре XenForo
        # ============================================
        
        # Паттерны для блоков с информацией пользователя
        user_info_patterns = [
            r'<dl[^>]*class="[^"]*pairs[^"]*"[^>]*>.*?</dl>',  # блоки пар ключ-значение
            r'<div[^>]*class="[^"]*memberHeader-info[^"]*"[^>]*>.*?</div>',  # header info
            r'<div[^>]*class="[^"]*userTitle[^"]*"[^>]*>.*?</div>',  # user title
        ]
        
        for pattern in user_info_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
            if matches:
                print(f"✅ Найдены блоки информации ({len(matches)} шт)")
                
                for block in matches:
                    # Ищем внутри блока "Активность"
                    if 'активность' in block.lower():
                        print(f"📦 Найден блок с активностью")
                        
                        # Извлекаем текст всего блока
                        block_text = re.sub('<[^<]+?>', ' ', block)
                        block_text = ' '.join(block_text.split())
                        
                        print(f"   Блок: {block_text[:200]}...")
                        
                        # Ищем строку с активностью
                        lines = block_text.split('.')
                        for line in lines:
                            if 'активность' in line.lower():
                                clean_line = line.strip()
                                if len(clean_line) > 10:
                                    return clean_line
        
        # ============================================
        # СПОСОБ 2: Ищем по разметке XenForo pairs
        # ============================================
        
        # Ищем все <dt> и <dd> пары
        dt_matches = list(re.finditer(r'<dt[^>]*>(.*?)</dt>', html, re.IGNORECASE | re.DOTALL))
        dd_matches = list(re.finditer(r'<dd[^>]*>(.*?)</dd>', html, re.IGNORECASE | re.DOTALL))
        
        if dt_matches and dd_matches:
            print(f"✅ Найдены dt/dd пары: {len(dt_matches)} dt, {len(dd_matches)} dd")
            
            # Ищем пару где <dt> содержит "Активность"
            for i, dt_match in enumerate(dt_matches):
                dt_text = re.sub('<[^<]+?>', '', dt_match.group(1)).strip()
                
                if 'активность' in dt_text.lower():
                    print(f"🎯 Найден dt с 'Активность': '{dt_text}'")
                    
                    # Берём соответствующий <dd>
                    if i < len(dd_matches):
                        dd_text = re.sub('<[^<]+?>', '', dd_matches[i].group(1)).strip()
                        result = f"{dt_text}: {dd_text}"
                        print(f"   Соответствующий dd: '{dd_text}'")
                        return result
        
        # ============================================
        # СПОСОБ 3: Ищем строку с активностью ПОСЛЕ регистрации
        # ============================================
        
        # Ищем "Регистрация" и берём текст ПОСЛЕ неё
        reg_pattern = r'Регистрация[^<]{10,150}'
        reg_match = re.search(reg_pattern, html, re.IGNORECASE)
        
        if reg_match:
            reg_end = reg_match.end()
            print(f"✅ Найдена регистрация, позиция окончания: {reg_end}")
            
            # Берём текст после регистрации (500 символов)
            after_reg = html[reg_end:reg_end + 500]
            
            # Ищем в этом тексте "Активность"
            activity_pattern = r'Активность[^<]{10,150}'
            activity_match = re.search(activity_pattern, after_reg, re.IGNORECASE)
            
            if activity_match:
                activity_text = activity_match.group(0)
                clean_activity = re.sub('<[^<]+?>', ' ', activity_text).strip()
                clean_activity = ' '.join(clean_activity.split())
                print(f"✅ Найдена активность после регистрации: '{clean_activity}'")
                return clean_activity
        
        # ============================================
        # СПОСОБ 4: Простой поиск по ключевым словам
        # ============================================
        
        # Разбиваем HTML на строки
        lines = html.split('\n')
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            # Ищем строку с активностью
            if 'активность' in line_lower and ('вчера' in line_lower or 'сегодня' in line_lower or 'только что' in line_lower or ':' in line_lower):
                # Чистим HTML
                clean_line = re.sub('<[^<]+?>', ' ', line).strip()
                clean_line = ' '.join(clean_line.split())
                
                if len(clean_line) > 10:
                    print(f"✅ Найдена в строке #{i}: '{clean_line}'")
                    return clean_line
        
        # ============================================
        # СПОСОБ 5: Ищем блок memberHeader-main
        # ============================================
        
        # На XenForo активность часто в memberHeader-main
        header_pattern = r'<div[^>]*class="[^"]*memberHeader-main[^"]*"[^>]*>.*?</div>'
        header_match = re.search(header_pattern, html, re.IGNORECASE | re.DOTALL)
        
        if header_match:
            header_html = header_match.group(0)
            print("✅ Найден memberHeader-main блок")
            
            # Ищем в нём активность
            if 'активность' in header_html.lower():
                # Извлекаем текст
                header_text = re.sub('<[^<]+?>', ' ', header_html).strip()
                header_text = ' '.join(header_text.split())
                
                # Берём часть с активностью
                for sentence in header_text.split('.'):
                    if 'активность' in sentence.lower():
                        clean_sentence = sentence.strip()
                        if len(clean_sentence) > 10:
                            return clean_sentence
        
        print("❌ Активность не найдена в HTML")
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
            print(f"✅ Страница загружена ({len(html)} символов)")
            
            # Сохраняем HTML для отладки
            with open("debug_page.html", "w", encoding="utf-8") as f:
                f.write(html)
            print("💾 HTML сохранён в debug_page.html")
            
            # ============================================
            # ПОИСК АКТИВНОСТИ "ТОЛЬКО ЧТО" (онлайн)
            # ============================================
            
            # Сначала извлекаем информацию об активности
            activity_text = extract_activity_from_html(html)
            print(f"\n📊 Извлечённая активность: '{activity_text}'")
            
            # Проверяем если "Только что"
            if activity_text and 'только что' in activity_text.lower():
                print("🎯 ОБНАРУЖЕНА АКТИВНОСТЬ 'ТОЛЬКО ЧТО'!")
                
                # Ищем местонахождение
                location = find_location(html)
                if location:
                    return {
                        'active': True,
                        'text': f"{activity_text}\n📍 {location}",
                        'location': location
                    }
                else:
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

def find_location(html):
    """Ищем где находится на форуме"""
    try:
        # После "Только что" часто идёт информация что просматривает
        lines = html.split('\n')
        
        for i, line in enumerate(lines):
            if "только что" in line.lower():
                # Смотрим следующие 2-3 строки
                for j in range(i+1, min(i+4, len(lines))):
                    next_line = lines[j].strip()
                    if next_line:
                        clean = re.sub('<[^<]+?>', ' ', next_line).strip()
                        clean = ' '.join(clean.split())
                        if clean and len(clean) > 5:
                            # Проверяем что это не технический текст
                            if not clean.startswith(('{', '[', 'http', '//')):
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
