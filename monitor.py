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
STATUS_FILE = "last_activity.txt"  # Простой текстовый файл

print(f"🔧 Конфигурация:")
print(f"  • BOT_TOKEN: {'✅ Есть' if BOT_TOKEN else '❌ НЕТ'}")
print(f"  • CHAT_ID: {CHAT_ID}")
print(f"  • URL: {URL}")

if not BOT_TOKEN or not CHAT_ID:
    print("\n❌ ОШИБКА: Не заданы токен или chat_id!")
    sys.exit(1)

def extract_activity_essence(html):
    """Извлекаем СУТЬ активности: день + время"""
    try:
        # Упрощённый поиск - ищем день и время
        html_clean = re.sub(r'<[^>]+>', ' ', html)
        html_clean = re.sub(r'\s+', ' ', html_clean)
        
        # Паттерны для извлечения сути
        patterns = [
            r'(Активность[^:]{0,5}:?\s*(Вчера|Сегодня|Только что)[^0-9]{0,10}(\d{1,2}[:.]\d{2}))',
            r'(Активность[^:]{0,5}:?\s*(\d{1,2}[:.]\d{2}))',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html_clean, re.IGNORECASE)
            if match:
                full_text = match.group(1)
                
                # Извлекаем СУТЬ: день + время
                essence = ""
                
                # День
                if 'вчера' in full_text.lower():
                    essence = "Вчера"
                elif 'сегодня' in full_text.lower():
                    essence = "Сегодня"
                elif 'только что' in full_text.lower():
                    essence = "Только что"
                else:
                    essence = "Недавно"
                
                # Время
                time_match = re.search(r'(\d{1,2})[:.](\d{2})', full_text)
                if time_match:
                    time_str = f"{time_match.group(1)}:{time_match.group(2)}"
                    if essence != "Только что":
                        essence += f" {time_str}"
                
                print(f"✅ Извлечена суть: '{essence}' из текста: '{full_text[:50]}...'")
                return {
                    'full_text': full_text.strip(),
                    'essence': essence,
                    'is_online': 'только что' in full_text.lower()
                }
        
        print("❌ Не удалось извлечь активность")
        return {
            'full_text': "Активность не определена",
            'essence': "Не определена",
            'is_online': False
        }
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return {
            'full_text': f"Ошибка: {str(e)[:50]}",
            'essence': "Ошибка",
            'is_online': False
        }

def load_last_activity():
    """Загружаем последнюю активность"""
    try:
        with open(STATUS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"📝 Предыдущая активность: '{data.get('essence', 'Нет')}'")
            return data
    except:
        print("📝 Предыдущая активность: Нет данных")
        return {
            'essence': '',
            'full_text': '',
            'is_online': False,
            'timestamp': ''
        }

def save_current_activity(activity_data):
    """Сохраняем текущую активность"""
    activity_data['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    with open(STATUS_FILE, 'w', encoding='utf-8') as f:
        json.dump(activity_data, f, ensure_ascii=False, indent=2)
    
    print(f"💾 Сохранено: '{activity_data['essence']}'")

def check_activity():
    """Проверяем активность"""
    print(f"\n🔍 Проверяем: {URL}")
    print(f"⏰ Время проверки: {datetime.now().strftime('%H:%M:%S')}")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(URL, headers=headers, timeout=10)
        
        if response.status_code == 200:
            html = response.text
            return extract_activity_essence(html)
        else:
            return {
                'full_text': f"Ошибка загрузки: {response.status_code}",
                'essence': "Ошибка",
                'is_online': False
            }
            
    except Exception as e:
        return {
            'full_text': f"Ошибка: {str(e)[:100]}",
            'essence': "Ошибка",
            'is_online': False
        }

def send_telegram_message(activity_data, is_alert=False):
    """Отправляем сообщение в Telegram"""
    try:
        current_time = datetime.now().strftime('%d.%m.%Y %H:%M:%S')
        
        if is_alert:
            message = f"""
<b>🚨 АКТИВНОСТЬ ОБНАРУЖЕНА!</b>

📅 <b>Время:</b> {current_time}
🔗 <b>Ссылка:</b> <a href="{URL}">{URL}</a>

📊 <b>Статус:</b>
<code>{activity_data['full_text']}</code>

🎯 <b>Пользователь в сети!</b>
"""
        else:
            message = f"""
<b>📊 Активность изменилась</b>

📅 <b>Время:</b> {current_time}
🔗 <b>Ссылка:</b> <a href="{URL}">{URL}</a>

📝 <b>Новый статус:</b>
<code>{activity_data['full_text']}</code>

🔄 <b>Изменение:</b> {activity_data.get('change_note', '')}
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
            print(f"✅ Сообщение отправлено!")
            return True
        else:
            print(f"❌ Ошибка отправки: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка Telegram: {e}")
        return False

def main():
    """Основная логика - ТОЛЬКО при реальных изменениях"""
    print("\n" + "=" * 60)
    
    # Загружаем предыдущую активность
    last_activity = load_last_activity()
    last_essence = last_activity.get('essence', '')
    last_full_text = last_activity.get('full_text', '')
    last_was_online = last_activity.get('is_online', False)
    
    # Проверяем текущую активность
    current_activity = check_activity()
    current_essence = current_activity.get('essence', '')
    current_full_text = current_activity.get('full_text', '')
    current_is_online = current_activity.get('is_online', False)
    
    print(f"\n📊 Сравнение активности:")
    print(f"  • Было: '{last_essence}' ({last_full_text[:50]}...)")
    print(f"  • Стало: '{current_essence}' ({current_full_text[:50]}...)")
    print(f"  • Онлайн был: {'✅ Да' if last_was_online else '❌ Нет'}")
    print(f"  • Онлайн стал: {'✅ Да' if current_is_online else '❌ Нет'}")
    
    # ============================================
    # КЛЮЧЕВАЯ ЛОГИКА: отправляем ТОЛЬКО при РЕАЛЬНЫХ изменениях
    # ============================================
    
    send_message = False
    is_alert = False
    change_note = ""
    
    # 1. ПЕРВЫЙ ЗАПУСК (нет предыдущих данных)
    if not last_essence:
        print("\n📝 Первый запуск - отправляем текущий статус")
        send_message = True
        change_note = "Первый запуск монитора"
    
    # 2. ИЗМЕНИЛСЯ СТАТУС "ОНЛАЙН" (Только что → что-то другое)
    elif last_was_online and not current_is_online:
        print("\n📊 Пользователь вышел из сети")
        send_message = True
        change_note = "Вышел из сети"
    
    # 3. ПОЯВИЛСЯ ОНЛАЙН (что-то другое → Только что)
    elif not last_was_online and current_is_online:
        print("\n🚨 ПОЯВИЛСЯ ОНЛАЙН!")
        send_message = True
        is_alert = True
        change_note = "Появился онлайн!"
    
    # 4. ИЗМЕНИЛСЯ ДЕНЬ активности (Вчера → Сегодня)
    elif 'вчера' in last_essence.lower() and 'сегодня' in current_essence.lower():
        print("\n📅 Изменился день активности (Вчера → Сегодня)")
        send_message = True
        change_note = "День изменился: Вчера → Сегодня"
    
    # 5. ИЗМЕНИЛОСЬ ВРЕМЯ (при том же дне)
    elif last_essence != current_essence and not current_is_online and not last_was_online:
        # Извлекаем время для сравнения
        last_time_match = re.search(r'(\d{1,2}:\d{2})', last_essence)
        current_time_match = re.search(r'(\d{1,2}:\d{2})', current_essence)
        
        if last_time_match and current_time_match:
            last_time = last_time_match.group(1)
            current_time = current_time_match.group(1)
            
            if last_time != current_time:
                print(f"\n⏰ Изменилось время: {last_time} → {current_time}")
                send_message = True
                change_note = f"Время изменилось: {last_time} → {current_time}"
            else:
                print(f"\nℹ️ Время не изменилось: {last_time}")
        else:
            print(f"\n📊 Изменилась суть активности: '{last_essence}' → '{current_essence}'")
            send_message = True
            change_note = f"Активность изменилась"
    
    # 6. ОШИБКА → НОРМА или НОРМА → ОШИБКА
    elif ('ошибка' in last_essence.lower() and 'ошибка' not in current_essence.lower()) or \
         ('ошибка' not in last_essence.lower() and 'ошибка' in current_essence.lower()):
        print(f"\n⚠️ Изменился статус ошибки")
        send_message = True
        change_note = "Статус ошибки изменился"
    
    else:
        print(f"\n✅ Активность НЕ изменилась: '{current_essence}'")
    
    # Добавляем заметку об изменении
    if change_note:
        current_activity['change_note'] = change_note
    
    # Отправляем сообщение если нужно
    if send_message:
        print(f"\n📨 Отправляем уведомление...")
        success = send_telegram_message(current_activity, is_alert=is_alert)
        
        if success:
            print("✅ Уведомление отправлено!")
        else:
            print("❌ Не удалось отправить")
    else:
        print("\n📭 Уведомление НЕ отправляется (активность не изменилась)")
    
    # Всегда сохраняем текущую активность
    save_current_activity(current_activity)
    
    print("\n" + "=" * 60)
    print("✅ Проверка завершена")

if __name__ == "__main__":
    main()
