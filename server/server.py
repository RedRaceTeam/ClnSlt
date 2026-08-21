#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ClnSIt Pro v7.0 — Серверная часть
Purge Labs · 2026
"""

import os
import sys
import json
import sqlite3
import hashlib
import base64
import time
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from cryptography.fernet import Fernet

app = Flask(__name__)
CORS(app)

# ===== КОНФИГ =====
DB_PATH = "licenses.db"
SECRET_KEY = os.environ.get("CLNSIT_SECRET", "PurgeLabs_S3cr3t_2026")

# ===== ИНИЦИАЛИЗАЦИЯ БАЗЫ =====
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Таблица лицензий
    c.execute('''
        CREATE TABLE IF NOT EXISTS licenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            hwid TEXT,
            expiry INTEGER NOT NULL,
            active INTEGER DEFAULT 1,
            created_at INTEGER,
            activated_at INTEGER,
            last_check INTEGER,
            version TEXT
        )
    ''')
    
    # Таблица версий кода
    c.execute('''
        CREATE TABLE IF NOT EXISTS code_versions (
            version TEXT PRIMARY KEY,
            encrypted_code TEXT NOT NULL,
            code_hash TEXT NOT NULL,
            created_at INTEGER NOT NULL,
            active INTEGER DEFAULT 1
        )
    ''')
    
    # Таблица логов
    c.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT,
            action TEXT,
            ip TEXT,
            timestamp INTEGER
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ База данных инициализирована")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def log_action(key: str, action: str, ip: str):
    conn = get_db()
    c = conn.cursor()
    c.execute(
        'INSERT INTO logs (key, action, ip, timestamp) VALUES (?, ?, ?, ?)',
        (key, action, ip, int(time.time()))
    )
    conn.commit()
    conn.close()

# ===== ШИФРОВАНИЕ =====
def encrypt_code(code: str, key: str) -> str:
    key_hash = hashlib.sha256(key.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(key_hash)
    cipher = Fernet(fernet_key)
    return cipher.encrypt(code.encode()).decode('utf-8')

def verify_license_key(key: str, hwid: str, version: str, ip: str) -> dict:
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT hwid, expiry, active FROM licenses WHERE key = ?', (key,))
    row = c.fetchone()
    conn.close()
    
    if not row:
        log_action(key, "verify_fail_not_found", ip)
        return {"valid": False, "error": "Ключ не найден"}
    
    saved_hwid, expiry, active = row
    
    if not active:
        log_action(key, "verify_fail_inactive", ip)
        return {"valid": False, "error": "Ключ заблокирован"}
    
    if expiry < int(time.time()):
        log_action(key, "verify_fail_expired", ip)
        return {"valid": False, "error": "Ключ истёк"}
    
    if saved_hwid and saved_hwid != hwid:
        log_action(key, "verify_fail_hwid_mismatch", ip)
        return {"valid": False, "error": "Ключ привязан к другому устройству"}
    
    if not saved_hwid:
        conn = get_db()
        c = conn.cursor()
        c.execute('UPDATE licenses SET hwid = ?, activated_at = ? WHERE key = ?', (hwid, int(time.time()), key))
        conn.commit()
        conn.close()
    
    conn = get_db()
    c = conn.cursor()
    c.execute('UPDATE licenses SET last_check = ? WHERE key = ?', (int(time.time()), key))
    conn.commit()
    conn.close()
    
    log_action(key, "verify_success", ip)
    
    return {
        "valid": True,
        "message": f"Лицензия активна до {datetime.fromtimestamp(expiry).strftime('%Y-%m-%d')}",
        "expiry": expiry
    }

# ===== API =====
@app.route('/api/verify', methods=['POST'])
def verify():
    data = request.json
    key = data.get('key')
    hwid = data.get('hwid')
    version = data.get('version')
    ip = request.remote_addr
    
    if not key:
        return jsonify({"valid": False, "error": "Ключ не указан"}), 400
    
    result = verify_license_key(key, hwid, version, ip)
    return jsonify(result)

@app.route('/api/download', methods=['POST'])
def download():
    data = request.json
    key = data.get('key')
    hwid = data.get('hwid')
    version = data.get('version')
    ip = request.remote_addr
    
    # Проверяем лицензию
    result = verify_license_key(key, hwid, version, ip)
    if not result.get("valid"):
        return jsonify({"error": "Невалидная лицензия"}), 403
    
    # Получаем код для версии
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT encrypted_code, code_hash FROM code_versions WHERE version = ? AND active = 1', (version,))
    row = c.fetchone()
    conn.close()
    
    if not row:
        log_action(key, "download_fail_no_version", ip)
        return jsonify({"error": f"Версия {version} не найдена"}), 404
    
    encrypted_code, code_hash = row
    
    log_action(key, "download_success", ip)
    
    return jsonify({
        "encrypted": encrypted_code,
        "version": version,
        "hash": code_hash,
        "expiry": result.get("expiry")
    })

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "version": "7.0.0", "time": int(time.time())})

@app.route('/api/stats', methods=['GET'])
def stats():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM licenses')
    total = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM licenses WHERE active = 1')
    active = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM logs WHERE action = "verify_success"')
    success = c.fetchone()[0]
    conn.close()
    
    return jsonify({
        "total_licenses": total,
        "active_licenses": active,
        "successful_verifications": success
    })

# ===== ЗАПУСК =====
if __name__ == "__main__":
    init_db()
    print("🚀 ClnSIt Pro Server v7.0")
    print(f"📊 База: {DB_PATH}")
    app.run(host='0.0.0.0', port=5000, debug=False)
