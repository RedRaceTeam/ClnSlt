#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
generate_keys.py — Генерация лицензионных ключей
Purge Labs · 2026
"""

import os
import sys
import sqlite3
import hashlib
import time
import random
from datetime import datetime

# ===== КОНФИГ =====
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'server', 'licenses.db')
SECRET_SALT = "PurgeLabs_S3cr3t_2026"

def generate_key(user_id: str, days: int = 365) -> str:
    """Генерирует ключ для пользователя"""
    expiry = int(time.time()) + (days * 24 * 60 * 60)
    data = f"{user_id}{expiry}{SECRET_SALT}{random.randint(1000, 9999)}"
    signature = hashlib.sha256(data.encode()).hexdigest()[:8]
    return f"CLN-{signature}-{expiry}"

def add_to_db(key: str, expiry: int):
    """Добавляет ключ в базу данных"""
    if not os.path.exists(DB_PATH):
        print("⚠️ База данных не найдена. Сначала запустите сервер.")
        return
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO licenses (key, expiry, active, created_at)
        VALUES (?, ?, 1, ?)
    ''', (key, expiry, int(time.time())))
    conn.commit()
    conn.close()

def main():
    print("="*50)
    print("  ClnSIt Pro — Генератор ключей")
    print("="*50)
    
    user_id = input("\n👤 ID пользователя (Telegram ID/ник): ").strip()
    if not user_id:
        print("❌ ID не может быть пустым")
        return
    
    days = input("📅 Срок действия (дней, по умолчанию 365): ").strip()
    days = int(days) if days.isdigit() else 365
    
    key = generate_key(user_id, days)
    expiry = int(key.split('-')[2])
    expiry_date = datetime.fromtimestamp(expiry).strftime('%Y-%m-%d')
    
    print("\n" + "="*50)
    print(f"🔑 Ключ для {user_id}:")
    print(f"   {key}")
    print(f"📅 Действителен до: {expiry_date}")
    print("="*50)
    
    save = input("\n💾 Добавить в базу данных? (y/n): ").strip().lower()
    if save == 'y':
        add_to_db(key, expiry)
        print("✅ Ключ добавлен в базу данных")
    
    save_file = input("💾 Сохранить в файл? (y/n): ").strip().lower()
    if save_file == 'y':
        filename = f"key_{user_id}_{datetime.now().strftime('%Y%m%d')}.txt"
        with open(filename, 'w') as f:
            f.write(f"Ключ: {key}\nДействителен до: {expiry_date}\nПользователь: {user_id}\n")
        print(f"✅ Сохранено в {filename}")

if __name__ == "__main__":
    main() 
