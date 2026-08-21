#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ClnSIt Pro v7.0 — Сервер
Purge Labs · 2026
"""

import os
import json
import sqlite3
import hashlib
import base64
import time
import random
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# ===== КОНФИГ =====
DB_PATH = os.environ.get("DB_PATH", "licenses.db")
SECRET_SALT = "PurgeLabs_S3cr3t_2026"
DEV_WORD = "purge_test_2026"

# ===== БАЗА ДАННЫХ =====

def init_db():
    # Создаём папку для БД, если её нет
    db_dir = os.path.dirname(DB_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS licenses (
        key TEXT PRIMARY KEY,
        hwid TEXT,
        expiry INTEGER,
        active INTEGER DEFAULT 1,
        created_at INTEGER
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS code (
        version TEXT PRIMARY KEY,
        encrypted TEXT,
        created_at INTEGER
    )''')
    conn.commit()
    conn.close()
    print(f"✅ База готова: {DB_PATH}")

# ===== ГЕНЕРАЦИЯ КЛЮЧЕЙ =====

def generate_key(user_id: str, days: int = 365) -> str:
    expiry = int(time.time()) + (days * 24 * 60 * 60)
    data = f"{user_id}{expiry}{SECRET_SALT}{random.randint(1000, 9999)}"
    signature = hashlib.sha256(data.encode()).hexdigest()[:8]
    return f"CLN-{signature}-{expiry}"

def add_key_to_db(key: str, expiry: int) -> bool:
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('INSERT INTO licenses (key, expiry, active, created_at) VALUES (?, ?, 1, ?)',
                  (key, expiry, int(time.time())))
        conn.commit()
        conn.close()
        return True
    except:
        return False

# ===== ПРОВЕРКА ЛИЦЕНЗИИ =====

def check_license(key: str, hwid: str) -> dict:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT hwid, expiry, active FROM licenses WHERE key = ?', (key,))
    row = c.fetchone()
    conn.close()
    
    if not row:
        return {"valid": False, "error": "Ключ не найден"}
    
    h, exp, act = row
    
    if not act:
        return {"valid": False, "error": "Ключ заблокирован"}
    
    if exp < int(time.time()):
        return {"valid": False, "error": "Ключ истёк"}
    
    if h and h != hwid:
        return {"valid": False, "error": "Ключ привязан к другому устройству"}
    
    if not h:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('UPDATE licenses SET hwid = ? WHERE key = ?', (hwid, key))
        conn.commit()
        conn.close()
    
    return {
        "valid": True,
        "expiry": exp,
        "message": f"Лицензия активна до {datetime.fromtimestamp(exp).strftime('%Y-%m-%d')}"
    }

# ===== API =====

@app.route('/api/verify', methods=['POST'])
def verify():
    data = request.json
    key = data.get('key')
    hwid = data.get('hwid')
    dev = data.get('dev')
    
    if dev == DEV_WORD:
        return jsonify({
            "valid": True,
            "message": "Тестовый режим (кодовое слово)",
            "is_dev": True
        })
    
    if not key:
        return jsonify({"valid": False, "error": "Нет ключа"}), 400
    
    return jsonify(check_license(key, hwid))

@app.route('/api/download', methods=['POST'])
def download():
    data = request.json
    key = data.get('key')
    hwid = data.get('hwid')
    version = data.get('version', '7.0.0')
    dev = data.get('dev')
    
    if dev == DEV_WORD:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT encrypted FROM code WHERE version = ?', (version,))
        row = c.fetchone()
        conn.close()
        if not row:
            return jsonify({"error": "Код не загружен"}), 404
        return jsonify({"encrypted": row[0], "is_dev": True})
    
    res = check_license(key, hwid)
    if not res.get("valid"):
        return jsonify({"error": "Лицензия невалидна"}), 403
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT encrypted FROM code WHERE version = ?', (version,))
    row = c.fetchone()
    conn.close()
    
    if not row:
        return jsonify({"error": "Версия не найдена"}), 404
    
    return jsonify({"encrypted": row[0]})

@app.route('/api/generate', methods=['POST'])
def generate():
    data = request.json
    user_id = data.get('user_id')
    days = data.get('days', 365)
    
    if not user_id:
        return jsonify({"error": "Нет user_id"}), 400
    
    key = generate_key(user_id, days)
    expiry = int(key.split('-')[2])
    
    if add_key_to_db(key, expiry):
        return jsonify({
            "key": key,
            "expiry": datetime.fromtimestamp(expiry).strftime('%Y-%m-%d'),
            "user_id": user_id
        })
    else:
        return jsonify({"error": "Ошибка сохранения"}), 500

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "time": int(time.time())})

@app.route('/api/upload_code', methods=['POST'])
def upload_code():
    data = request.json
    version = data.get('version', '7.0.0')
    encrypted = data.get('encrypted')
    
    if not encrypted:
        return jsonify({"error": "Нет кода"}), 400
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO code (version, encrypted, created_at) VALUES (?, ?, ?)',
              (version, encrypted, int(time.time())))
    conn.commit()
    conn.close()
    
    return jsonify({"status": "ok", "version": version})

# ===== ЗАПУСК =====

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    print("="*50)
    print("🚀 ClnSIt Pro Server v7.0")
    print(f"📊 База: {DB_PATH}")
    print(f"🔧 Кодовое слово: {DEV_WORD}")
    print(f"🌐 Порт: {port}")
    print("="*50)
    app.run(host='0.0.0.0', port=port, debug=False)
