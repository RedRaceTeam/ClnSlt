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

def generate_key(user_id: str, days: int = 365) -> str:
    """Генерирует ключ"""
    SECRET_SALT = "PurgeLabs_S3cr3t_2026"
    expiry = int(time.time()) + (days * 24 * 60 * 60)
    data = f"{user_id}{expiry}{SECRET_SALT}{random.randint(1000, 9999)}"
    signature = hashlib.sha256(data.encode()).hexdigest()[:8]
    return f"CLN-{signature}-{expiry}"

def add_key_to_db(key: str, expiry: int):
    """Добавляет ключ в базу данных"""
    db_path = os.path.join(os.path.dirname(__file__), '..', 'server', 'licenses.db')
    
    if not os.path.exists(db_path):
        print("⚠️ База данных не найдена.")
        return
    
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    c.execute('''
        INSERT INTO licenses (key, expiry, active, created_at)
        VALUES (?, ?, 1, ?)
    ''', (key, expiry, int(time.time())))
    
    conn.commit()
    conn.close()
    
    print(f"✅ Ключ добавлен в базу")

def main():
    print("🔑 Генератор ключей ClnSIt Pro")
    print("="*50)
    
    user_id = input("👤 ID пользователя: ").strip()
    if not user_id:
        print("❌ ID не может быть пустым")
        return
    
    days = input("📅 Срок (дней, по умолчанию 365): ").strip()
    days = int(days) if days.isdigit() else 365
    
    key = generate_key(user_id, days)
    expiry = int(key.split('-')[2])
    expiry_date = datetime.fromtimestamp(expiry).strftime('%Y-%m-%d')
    
    print("\n" + "="*50)
    print(f"🔑 Ключ: {key}")
    print(f"📅 Действителен до: {expiry_date}")
    print("="*50)
    
    add = input("\n💾 Добавить в базу? (y/n): ").strip().lower()
    if add == 'y':
        add_key_to_db(key, expiry)
    
    save = input("💾 Сохранить в файл? (y/n): ").strip().lower()
    if save == 'y':
        filename = f"key_{user_id}.txt"
        with open(filename, 'w') as f:
            f.write(f"Ключ: {key}\nДействителен до: {expiry_date}\n")
        print(f"✅ Сохранено в {filename}")

if __name__ == "__main__":
    main()
