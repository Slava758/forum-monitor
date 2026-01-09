import requests
import os
import sys
from datetime import datetime
import re
import time

print("=" * 60)
print("🚀 МОНИТОР АКТИВНОСТИ GTA5RP")
print("=" * 60)

# Получаем секреты
BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')
URL = "https://forum.gta5rp.com/members/adminadminov.6/"

print(f"🔧 Конфигурация:")
print(f"  • BOT_TOKEN: {'✅ Есть' if BOT_TOKEN else '❌ НЕТ'}")
print(f"  • CHAT_ID: {CHAT_ID}")
print(f"  • URL: {URL}")

# Проверяем настройки
if not BOT_TOKEN or not CHAT_ID:
    print("\n❌ ОШИБКА: Не заданы токен или chat_id!")
    sys.exit(1)

def check_activity():
    """Проверяем активность - ТОЧНЫЙ ПОИСК"""
    print(f"\n🔍 Проверяем: {URL}")
    print(f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(URL, headers=headers, timeout=10)
        
        if response.status_code == 200:
            html = response.text
            
            # Сохраняем для отладки
            with open("debug.html", "w", encoding="utf-8") as f:
                f.write(html[:10000])  # Первые 10000 символов
            
            print(f"✅ Страница загружена ({len(html)} символов)")
            
            # ============================================
            # КЛЮЧЕВОЙ ПОИСК: "Активность: Только что"
            # ============================================
            
            # Вариант 1: Точное совпадение "Активность: Только что"
            if "Активность: Только что" in html:
                print("🎯 ТОЧНОЕ СОВПАДЕНИЕ: 'Активность: Только что'")
                
                # Ищем что делает на форуме
                location = find_location(html)
                
                if location:
                    return {
                        'active': True,
                        'text': f"Активность: Только что\n{location}",
                        'location': location
                    }
                else:
                    return {
                        'active': True,
                        'text': "Активность: Только что (местонахождение не найдено)",
                        'location': None
                    }
            
            # Вариант 2: Поиск с разными регистрами и пробелами
            import re
            
            # Паттерны для поиска активности
            patterns = [
                r'Активность:\s*Только что',      # с двоеточием и пробелом
                r'Активность\s*Только что',       # без двоеточия
                r'Активность:\s*только что',      # маленькие буквы
                r'Активность\s*только что',       # без двоеточия, маленькие
            ]
            
            for pattern in patterns:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    found_text = match.group(0)
                    print(f"🎯 РЕГУЛЯРНОЕ ВЫРАЖЕНИЕ: '{found_text}'")
                    
                    # Ищем что делает на форуме
                    location = find_location(html)
                    
                    if location:
                        return {
                            'active': True,
                            'text': f"{found_text}\n{location}",
                            'location': location
                        }
                    else:
                        return {
                            'active': True,
                            'text': f"{found_text} (местонахождение не найдено)",
                            'location': None
                        }
            
            # Вариант 3: Поиск "Только что" рядом с "Активность"
            # Ищем в пределах 50 символов
            activity_match = re.search(r'Активность[^<]{0,50}', html, re.IGNORECASE)
            if activity_match:
                activity_text = activity_match.group(0)
                if "только что" in activity_text.lower():
                    print(f"🎯 БЛИЗКОЕ СОВПАДЕНИЕ: '{activity_text.strip()}'")
                    
                    location = find_location(html)
                    
                    if location:
                        return {
                            'active': True,
                            'text': f"{activity_text.strip()}\n{location}",
                            'location': location
                        }
                    else:
                        return {
                            'active': True,
                            'text': f"{activity_text.strip()} (местонахождение не найдено)",
                            'location': None
                        }
            
            # Если не нашли активность "Только что", показываем текущий статус
            current_status = find_current_status(html)
            print(f"📊 Текущий статус: {current_status}")
            
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
        # Ищем текст после активности (следующая строка или близко)
        lines = html.split('\n')
        
        for i, line in enumerate(lines):
            if "только что" in line.lower() and "активность" in line.lower():
                # Смотрим следующие 3 строки
                for j in range(i+1, min(i+4, len(lines))):
                    next_line = lines[j].strip()
                    # Убираем HTML теги
                    clean_line = re.sub('<[^<]+?>', '', next_line).strip()
                    if clean_line and len(clean_line) > 5:
                        # Проверяем что это не пустая строка и не техническая информация
                        if not clean_line.startswith(('{', '[', '<', 'http')):
                            print(f"📍 Найдено местонахождение: '{clean_line[:100]}'")
                            return clean_line
                
                # Если в следующих строках не нашли, ищем в той же строке после "Только что"
                line_text = re.sub('<[^<]+?>', '', line).strip()
                parts = line_text.split('Только что')
                if len(parts) > 1 and parts[1].strip():
                    location = parts[1].strip()
                    print(f"📍 Местонахождение в той же строке: '{location[:100]}'")
                    return location
        
        print("ℹ️ Местонахождение не найдено")
        return None
        
    except Exception as e:
        print(f"Ошибка поиска местонахождения: {e}")
        return None

def find_current_status(html):
    """Находим текущий статус активности"""
    try:
        # Ищем любую информацию об активности
        patterns = [
            r'Активность[^<]*',          # Активность что-то
            r'Последняя активность[^<]*', # Последняя активность
            r'Был\(а\) на сайте[^<]*',    # Был(а) на сайте
            r'Заходил\(а\)[^<]*',         # Заходил(а)
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                status = match.group(0)
                # Чистим от HTML тегов
                clean_status = re.sub('<[^<]+?>', '', status).strip()
                if clean_status:
                    return clean_status
        
        return "Не удалось определить активность"
        
    except:
        return "Ошибка определения статуса"

def send_to_telegram(result):
    """Отправляем в Telegram"""
    try:
        current_time = datetime.now().strftime('%d.%m.%Y %H:%M:%S')
        
        if result['active']:
            # УВЕДОМЛЕНИЕ ОБ АКТИВНОСТИ
            telegram_msg = f"""
<b>🚨 АКТИВНОСТЬ ОБНАРУЖЕНА!</b>

📅 <b>Время:</b> {current_time}
🔗 <b>Ссылка:</b> {URL}

📊 <b>Статус:</b>
<code>{result['text']}</code>

🎯 <b>Пользователь в сети!</b>

#мониторинг #активность
"""
        else:
            # ТЕСТОВОЕ УВЕДОМЛЕНИЕ
            telegram_msg = f"""
<b>🔄 Проверка монитора</b>

📅 <b>Время:</b> {current_time}
🔗 <b>Ссылка:</b> {URL}

📊 <b>Текущий статус:</b>
<code>{result['text']}</code>

✅ Монитор работает.
При обнаружении "Активность: Только что"
будет отправлено уведомление.

#мониторинг #проверка
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
            print(f"✅ Сообщение отправлено в Telegram!")
            return True
        else:
            print(f"❌ Ошибка отправки: {response.status_code}")
            print(f"Ответ: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка Telegram: {e}")
        return False

# Основная программа
if __name__ == "__main__":
    print("\n" + "=" * 60)
    
    result = check_activity()
    
    print(f"\n📊 Результат проверки:")
    print(f"  • Активен: {'✅ ДА' if result['active'] else '❌ НЕТ'}")
    print(f"  • Текст: {result['text'][:100]}...")
    if result['location']:
        print(f"  • Местонахождение: {result['location'][:100]}...")
    
    print("\n📨 Отправляем в Telegram...")
    
    # Отправляем всегда (тест при запуске, уведомление при активности)
    success = send_to_telegram(result)
    
    if success:
        if result['active']:
            print("✅ УВЕДОМЛЕНИЕ ОБ АКТИВНОСТИ ОТПРАВЛЕНО!")
        else:
            print("✅ Тестовое сообщение отправлено!")
    else:
        print("❌ Не удалось отправить сообщение")
    
    print("\n" + "=" * 60)
    print("✅ Скрипт завершен")
