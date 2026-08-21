#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ClnSIt Professional v7.0 — Клиентская часть
Purge Labs · 2026

Архитектура: клиент-сервер
Лицензия: OL-CC v2.0
"""

import os
import sys
import json
import hashlib
import base64
import time
import platform
import subprocess
import tempfile
from datetime import datetime
from typing import Dict, Optional

try:
    import requests
except ImportError:
    print("❌ Установите requests: pip install requests")
    sys.exit(1)

try:
    from cryptography.fernet import Fernet
except ImportError:
    print("❌ Установите cryptography: pip install cryptography")
    sys.exit(1)

VERSION = "7.0.0"
SERVER_URL = "https://api.purgelabs.com"
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".clnsit")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
LICENSE_FILE = os.path.join(CONFIG_DIR, "license.key")

LOGO = """
┌─────────────────────────────────────────────────────────────┐
│  ██████╗██╗     ███╗   ██╗███████╗██╗████████╗            │
│  ██╔════╝██║     ████╗  ██║██╔════╝██║╚══██╔══╝            │
│  ██║     ██║     ██╔██╗ ██║███████╗██║   ██║               │
│  ██║     ██║     ██║╚██╗██║╚════██║██║   ██║               │
│  ╚██████╗███████╗██║ ╚████║███████║██║   ██║               │
│   ╚═════╝╚══════╝╚═╝  ╚═══╝╚══════╝╚═╝   ╚═╝               │
│                                                             │
│  ██████╗ ██████╗  ██████╗                                    │
│  ██╔══██╗██╔══██╗██╔═══██╗                                   │
│  ██████╔╝██████╔╝██║   ██║                                   │
│  ██╔═══╝ ██╔══██╗██║   ██║                                   │
│  ██║     ██║  ██║╚██████╔╝                                   │
│  ╚═╝     ╚═╝  ╚═╝ ╚═════╝                                    │
│                                                             │
│            ClnSIt Professional v7.0.0                       │
│                   Purge Labs · 2026                         │
│                                                             │
│  ⚡ OSINT Engine · 🔍 300+ Sources · 🛡️ OL-CC v2.0        │
└─────────────────────────────────────────────────────────────┘
"""

DISCLAIMER = """
═══════════════════════════════════════════════════════════════
  ⚠️  ПРИНЯТИЕ УСЛОВИЙ ИСПОЛЬЗОВАНИЯ  ⚠️
═══════════════════════════════════════════════════════════════

  ClnSIt Professional — OSINT-инструмент для образовательных и
  исследовательских целей.

  Используя программу, вы подтверждаете, что:

  1. Используете её ТОЛЬКО в законных целях
  2. Несёте ПОЛНУЮ ответственность за свои действия
  3. Не будете использовать для сбора данных без согласия
  4. Ознакомлены с лицензией OL-CC v2.0
  5. Понимаете, что программа предоставляется "КАК ЕСТЬ"

  Лицензия: OL-CC v2.0
  Контакт: @PurgeLabs

═══════════════════════════════════════════════════════════════

  [1] — Я принимаю условия и продолжаю
  [2] — Я не принимаю условия (выход)

═══════════════════════════════════════════════════════════════
"""

def get_hwid() -> str:
    hwid_data = []
    try:
        if platform.system() == "Windows":
            cmd = "wmic cpu get processorid"
            output = subprocess.check_output(cmd, shell=True).decode()
            hwid_data.append(output.strip().split('\n')[1].strip())
        else:
            with open("/proc/cpuinfo", "r") as f:
                for line in f:
                    if "Serial" in line:
                        hwid_data.append(line.split(":")[1].strip())
                        break
    except:
        pass
    
    try:
        if platform.system() == "Windows":
            cmd = "ipconfig /all"
            output = subprocess.check_output(cmd, shell=True).decode()
            for line in output.split('\n'):
                if "Physical Address" in line:
                    hwid_data.append(line.split(":")[1].strip())
                    break
        else:
            cmd = "ip link show | grep ether | head -1"
            output = subprocess.check_output(cmd, shell=True).decode()
            hwid_data.append(output.strip().split()[1])
    except:
        pass
    
    try:
        hwid_data.append(platform.node())
    except:
        pass
    
    combined = "|".join(hwid_data)
    return hashlib.sha256(combined.encode()).hexdigest()[:16]

def check_config() -> bool:
    if not os.path.exists(CONFIG_FILE):
        return False
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            return config.get('disclaimer_accepted', False)
    except:
        return False

def save_config():
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, 'w') as f:
        json.dump({
            'disclaimer_accepted': True,
            'accepted_at': time.time(),
            'version': VERSION
        }, f)

def print_disclaimer() -> bool:
    print(DISCLAIMER)
    while True:
        choice = input("> ").strip()
        if choice == "1":
            save_config()
            print("\n✅ Условия приняты. Запуск программы...")
            time.sleep(1)
            return True
        elif choice == "2":
            print("\n❌ Условия не приняты. Выход...")
            sys.exit(0)
        else:
            print("❌ Неверный выбор. Введите 1 или 2")

def load_license() -> Optional[str]:
    if not os.path.exists(LICENSE_FILE):
        return None
    try:
        with open(LICENSE_FILE, 'r') as f:
            return f.read().strip()
    except:
        return None

def save_license(key: str):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(LICENSE_FILE, 'w') as f:
        f.write(key)

def verify_license(key: str, hwid: str) -> Dict:
    try:
        response = requests.post(
            f"{SERVER_URL}/api/verify",
            json={
                "key": key,
                "hwid": hwid,
                "version": VERSION,
                "timestamp": int(time.time())
            },
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {"valid": False, "error": f"Сервер вернул {response.status_code}"}
    except requests.exceptions.ConnectionError:
        return {"valid": False, "error": "Не удалось подключиться к серверу"}
    except Exception as e:
        return {"valid": False, "error": str(e)}

def download_code(key: str, hwid: str) -> Optional[str]:
    try:
        response = requests.post(
            f"{SERVER_URL}/api/download",
            json={
                "key": key,
                "hwid": hwid,
                "version": VERSION
            },
            timeout=30
        )
        if response.status_code != 200:
            return None
        data = response.json()
        return data.get("encrypted")
    except:
        return None

def decrypt_code(encrypted: str, key: str) -> Optional[str]:
    try:
        key_hash = hashlib.sha256(key.encode()).digest()
        fernet_key = base64.urlsafe_b64encode(key_hash)
        cipher = Fernet(fernet_key)
        return cipher.decrypt(encrypted.encode()).decode('utf-8')
    except:
        return None

def print_help():
    print("""
┌─────────────────────────────────────────────────────────────┐
│  ClnSIt Pro — Доступные команды                           │
├─────────────────────────────────────────────────────────────┤
│  search <никнейм>     — Поиск по никнейму                 │
│  email <email>        — Проверка email (HIBP)             │
│  phone <номер>        — Проверка телефона                 │
│  whois <домен>        — WHOIS домена                     │
│  dns <домен>          — DNS запросы                      │
│  cluster              — Кластеризация найденных профилей  │
│  report               — Сохранить отчёт                  │
│  help                 — Эта справка                      │
│  exit                 — Выход                            │
└─────────────────────────────────────────────────────────────┘
""")

def main():
    print(LOGO)
    if not check_config():
        print_disclaimer()
    
    hwid = get_hwid()
    saved_key = load_license()
    
    if saved_key:
        print("\n🔑 Проверка лицензии...")
        result = verify_license(saved_key, hwid)
        if result.get("valid"):
            print(f"✅ {result.get('message', 'Лицензия активна')}")
            print("📦 Загрузка кода...")
            encrypted = download_code(saved_key, hwid)
            if encrypted:
                code = decrypt_code(encrypted, saved_key)
                if code:
                    print("✅ Запуск...\n")
                    exec(code)
                    return
                else:
                    print("❌ Ошибка расшифровки кода")
            else:
                print("❌ Ошибка загрузки кода")
        else:
            print(f"❌ {result.get('error', 'Неверный ключ')}")
            if os.path.exists(LICENSE_FILE):
                os.remove(LICENSE_FILE)
    
    print("""
┌─────────────────────────────────────────────────────────────┐
│  Для активации ClnSIt Pro введите лицензионный ключ        │
│  Получить ключ: @PurgeLabs                                │
└─────────────────────────────────────────────────────────────┘
""")
    
    key = input("\n🔑 Введите ключ: ").strip()
    if not key:
        print("❌ Ключ не может быть пустым")
        sys.exit(1)
    
    result = verify_license(key, hwid)
    if not result.get("valid"):
        print(f"❌ {result.get('error', 'Неверный ключ')}")
        sys.exit(1)
    
    save_license(key)
    print(f"✅ {result.get('message', 'Лицензия активирована')}")
    print("📦 Загрузка кода...")
    encrypted = download_code(key, hwid)
    if not encrypted:
        print("❌ Ошибка загрузки кода. Проверьте подключение.")
        sys.exit(1)
    code = decrypt_code(encrypted, key)
    if not code:
        print("❌ Ошибка расшифровки кода.")
        sys.exit(1)
    print("✅ Запуск...\n")
    exec(code)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️ Прервано")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
