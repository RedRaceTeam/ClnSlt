#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
encrypt_code.py — Шифрует код перед загрузкой на сервер
Purge Labs · 2026
"""

import os
import sys
import json
import hashlib
import base64
import sqlite3
from cryptography.fernet import Fernet

# ===== КОНФИГ =====
SECRET_KEY = "PurgeLabs_S3cr3t_2026"

def encrypt_file(input_file: str, output_file: str = None):
    """Шифрует файл и сохраняет результат"""
    
    # Читаем код
    with open(input_file, 'r', encoding='utf-8') as f:
        code = f.read()
    
    # Шифруем
    key_hash = hashlib.sha256(SECRET_KEY.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(key_hash)
    cipher = Fernet(fernet_key)
    
    encrypted = cipher.encrypt(code.encode()).decode('utf-8')
    
    # Сохраняем
    if output_file is None:
        output_file = input_file.replace('.py', '.enc')
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(encrypted)
    
    # Хеш для проверки целостности
    code_hash = hashlib.sha256(code.encode()).hexdigest()
    
    print(f"✅ Файл {input_file} зашифрован -> {output_file}")
    print(f"📊 Хеш: {code_hash}")
    print(f"📊 Размер: {len(encrypted)} символов")
    
    return encrypted, code_hash

def add_to_db(version: str, encrypted: str, code_hash: str):
    """Добавляет версию в базу данных"""
    db_path = os.path.join(os.path.dirname(__file__), '..', 'server', 'licenses.db')
    
    if not os.path.exists(db_path):
        print("⚠️ База данных не найдена. Сначала запустите сервер.")
        return
    
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    c.execute('''
        INSERT OR REPLACE INTO code_versions (version, encrypted_code, code_hash, created_at, active)
        VALUES (?, ?, ?, ?, 1)
    ''', (version, encrypted, code_hash, int(time.time())))
    
    conn.commit()
    conn.close()
    
    print(f"✅ Версия {version} добавлена в базу данных")

if __name__ == "__main__":
    import time
    
    if len(sys.argv) < 2:
        print("Использование: python encrypt_code.py <файл.py> [версия]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    version = sys.argv[2] if len(sys.argv) > 2 else "7.0.0"
    
    encrypted, code_hash = encrypt_file(input_file)
    add_to_db(version, encrypted, code_hash)
