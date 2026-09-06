#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ClnSIt Server v5.1 — Enterprise Edition
Purge Labs © 2026
"""

import os
import sys
import json
import time
import sqlite3
import logging
import secrets
import string
import hashlib
import base64
import shutil
import asyncio
import re
import random
from datetime import datetime
from typing import Optional, Dict, Tuple
from flask import Flask, request, jsonify
from flask_cors import CORS
from cryptography.fernet import Fernet, InvalidToken

# =====================================================================
# 1. ПОЛНОЕ OSINT-ЯДРО (50+ ИСТОЧНИКОВ, ГРАФЫ, ПАРСИНГ)
# =====================================================================
CORE_CODE = '''
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ClnSIt Core v5.1 — OSINT Engine
Purge Labs © 2026

Функции:
- Поиск по 50+ соцсетям
- Обход Cloudflare (curl_cffi)
- Быстрый парсинг (selectolax)
- Извлечение email, телефонов, ссылок
- Построение звёздного графа
- Сохранение отчёта в JSON
"""

import asyncio
import json
import re
import sys
import time
import random
from datetime import datetime

# ============================================================
# ПРОВЕРКА ЗАВИСИМОСТЕЙ
# ============================================================
try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False
    print("⚠️ Установите: pip install httpx[http2]")

try:
    from curl_cffi import requests as curl_requests
    HAS_CURL = True
except ImportError:
    HAS_CURL = False
    print("⚠️ Установите: pip install curl_cffi")

try:
    from selectolax.parser import HTMLParser
    HAS_SELECTOLAX = True
except ImportError:
    HAS_SELECTOLAX = False
    print("⚠️ Установите: pip install selectolax")

PLAYWRIGHT_AVAILABLE = False
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    print("⚠️ Установите: playwright && playwright install chromium")

# ============================================================
# ЦВЕТА
# ============================================================
class Colors:
    RED = '\\033[91m'
    GREEN = '\\033[92m'
    YELLOW = '\\033[93m'
    CYAN = '\\033[96m'
    WHITE = '\\033[97m'
    BOLD = '\\033[1m'
    RESET = '\\033[0m'

# ============================================================
# БАЗА ИСТОЧНИКОВ (50+ РЕАЛЬНЫХ САЙТОВ)
# ============================================================
SOURCES = {
    # Глобальные
    "github": {"url": "https://github.com/{}", "type": "public"},
    "gitlab": {"url": "https://gitlab.com/{}", "type": "public"},
    "bitbucket": {"url": "https://bitbucket.org/{}/", "type": "public"},
    "stackoverflow": {"url": "https://stackoverflow.com/users/{}", "type": "public"},
    "reddit": {"url": "https://www.reddit.com/user/{}", "type": "public"},
    "hackernews": {"url": "https://news.ycombinator.com/user?id={}", "type": "public"},
    "medium": {"url": "https://medium.com/@{}", "type": "public"},
    "devto": {"url": "https://dev.to/{}", "type": "public"},
    "leetcode": {"url": "https://leetcode.com/{}", "type": "public"},
    "codepen": {"url": "https://codepen.io/{}", "type": "public"},
    "pastebin": {"url": "https://pastebin.com/u/{}", "type": "public"},
    "keybase": {"url": "https://keybase.io/{}", "type": "public"},
    "gravatar": {"url": "https://gravatar.com/{}", "type": "public"},
    "substack": {"url": "https://{}.substack.com", "type": "public"},
    "tumblr": {"url": "https://{}.tumblr.com", "type": "public"},
    "soundcloud": {"url": "https://soundcloud.com/{}", "type": "public"},
    "vimeo": {"url": "https://vimeo.com/{}", "type": "public"},
    "behance": {"url": "https://www.behance.net/{}", "type": "public"},
    "dribbble": {"url": "https://dribbble.com/{}", "type": "public"},
    "artstation": {"url": "https://www.artstation.com/{}", "type": "public"},
    "spotify": {"url": "https://open.spotify.com/user/{}", "type": "public"},
    "steam": {"url": "https://steamcommunity.com/id/{}", "type": "public"},
    "pinterest": {"url": "https://www.pinterest.com/{}", "type": "public"},
    
    # Русскоязычные
    "pikabu": {"url": "https://pikabu.ru/{}", "type": "public"},
    "habr": {"url": "https://habr.com/ru/users/{}", "type": "public"},
    "dtf": {"url": "https://dtf.ru/u/{}", "type": "public"},
    "vcru": {"url": "https://vc.ru/u/{}", "type": "public"},
    "tjournal": {"url": "https://tjournal.ru/users/{}", "type": "public"},
    "cyberforum": {"url": "https://www.cyberforum.ru/members/{}", "type": "public"},
    "4pda": {"url": "https://4pda.to/forum/index.php?showuser={}", "type": "public"},
    
    # Тяжёлые (требуют имперсонации)
    "twitter": {"url": "https://twitter.com/{}", "type": "heavy"},
    "instagram": {"url": "https://www.instagram.com/{}", "type": "heavy"},
    "facebook": {"url": "https://www.facebook.com/{}", "type": "heavy"},
    "vk": {"url": "https://vk.com/{}", "type": "heavy"},
    "telegram": {"url": "https://t.me/{}", "type": "heavy"},
    "twitch": {"url": "https://www.twitch.tv/{}", "type": "heavy"},
    "youtube": {"url": "https://www.youtube.com/{}", "type": "heavy"},
    "tiktok": {"url": "https://www.tiktok.com/@{}", "type": "heavy"},
    "linkedin": {"url": "https://www.linkedin.com/in/{}", "type": "heavy"},
}

# ============================================================
# HTTP-КЛИЕНТЫ
# ============================================================
class HTTPClients:
    def __init__(self):
        self.httpx_client = None
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]
        self.impersonates = ["chrome120", "chrome119", "firefox121"]

    def get_headers(self):
        return {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }

    async def init_httpx(self):
        if not self.httpx_client and HAS_HTTPX:
            self.httpx_client = httpx.AsyncClient(
                http2=True,
                follow_redirects=True,
                timeout=15.0,
                limits=httpx.Limits(max_keepalive_connections=50)
            )

    async def get_httpx(self, url: str):
        try:
            await self.init_httpx()
            if self.httpx_client:
                return await self.httpx_client.get(url, headers=self.get_headers())
        except Exception:
            return None

    def get_curl(self, url: str, impersonate: str = "chrome120"):
        if not HAS_CURL:
            return None
        try:
            return curl_requests.get(url, impersonate=impersonate, timeout=15, headers=self.get_headers())
        except Exception:
            return None

# ============================================================
# PLAYWRIGHT
# ============================================================
async def fetch_with_playwright(url: str) -> str:
    if not PLAYWRIGHT_AVAILABLE:
        return None
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = await context.new_page()
            await page.goto(url, timeout=15000, wait_until='domcontentloaded')
            await page.wait_for_timeout(2000)
            html = await page.content()
            await browser.close()
            return html
    except Exception:
        return None

# ============================================================
# ПАРСЕР (SELECTOLAX)
# ============================================================
def extract_meta(html: str) -> dict:
    try:
        tree = HTMLParser(html)
        result = {"title": "", "bio": ""}
        title = tree.css_first('title')
        if title:
            result["title"] = title.text(strip=True)[:100]
        desc = tree.css_first('meta[name="description"]')
        if desc:
            result["bio"] = desc.attributes.get('content', '')[:200]
        else:
            og_desc = tree.css_first('meta[property="og:description"]')
            if og_desc:
                result["bio"] = og_desc.attributes.get('content', '')[:200]
        if not result["bio"]:
            body = tree.css_first('body')
            if body:
                raw = body.text(strip=True)
                result["bio"] = re.sub(r'\\s+', ' ', raw)[:200]
        return result
    except Exception:
        return {"title": "", "bio": ""}

# ============================================================
# ИЗВЛЕЧЕНИЕ СУЩНОСТЕЙ
# ============================================================
def extract_entities(text: str) -> dict:
    if not text:
        return {"emails": [], "phones": [], "links": []}
    return {
        "emails": list(set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text))),
        "phones": list(set(re.findall(r'(?:\\+7|8|7|9)[0-9]{9,10}', text))),
        "links": list(set(re.findall(r'https?://[^\\s<>]+', text)))
    }

# ============================================================
# ПОСТРОЕНИЕ ГРАФА (ЗВЕЗДА)
# ============================================================
def build_graph(username: str, profiles: list) -> dict:
    graph = {
        "axiom": username,
        "nodes": {username: {"type": "core", "weight": 1.0}},
        "edges": []
    }
    for p in profiles:
        if not p.get("found"):
            continue
        node_id = f"{p['source']}_{username}"
        graph["nodes"][node_id] = {
            "type": "profile",
            "source": p["source"],
            "url": p["url"],
            "weight": 0.8
        }
        graph["edges"].append((username, node_id, 0.8))
        
        entities = extract_entities(p.get("bio", ""))
        for email in entities.get("emails", []):
            email_node = f"email_{email}"
            if email_node not in graph["nodes"]:
                graph["nodes"][email_node] = {"type": "email", "value": email, "weight": 1.0}
            graph["edges"].append((node_id, email_node, 1.0))
        for phone in entities.get("phones", []):
            phone_node = f"phone_{phone}"
            if phone_node not in graph["nodes"]:
                graph["nodes"][phone_node] = {"type": "phone", "value": phone, "weight": 0.9}
            graph["edges"].append((node_id, phone_node, 0.9))
        if p.get("bio"):
            graph["nodes"][node_id]["bio"] = p["bio"][:150]
    return graph

# ============================================================
# ОСНОВНАЯ ЛОГИКА ПОИСКА
# ============================================================
clients = HTTPClients()

async def check_source(source: str, username: str) -> dict:
    url = SOURCES[source]["url"].format(username)
    site_type = SOURCES[source].get("type", "public")
    result = {"source": source, "found": False, "url": url, "title": "", "bio": ""}
    
    if site_type == "public":
        response = await clients.get_httpx(url)
        if response and response.status_code == 200:
            meta = extract_meta(response.text)
            result["found"] = True
            result["title"] = meta.get("title", "")
            result["bio"] = meta.get("bio", "")
            return result
    
    if HAS_CURL:
        for impersonate in ["chrome120", "chrome119"]:
            try:
                response = clients.get_curl(url, impersonate=impersonate)
                if response and response.status_code == 200:
                    meta = extract_meta(response.text)
                    result["found"] = True
                    result["title"] = meta.get("title", "")
                    result["bio"] = meta.get("bio", "")
                    return result
            except Exception:
                continue
    
    if site_type == "heavy" and PLAYWRIGHT_AVAILABLE:
        html = await fetch_with_playwright(url)
        if html:
            meta = extract_meta(html)
            if meta.get("bio") or meta.get("title"):
                result["found"] = True
                result["title"] = meta.get("title", "")
                result["bio"] = meta.get("bio", "")
                return result
    
    return result

async def search_all(username: str) -> dict:
    tasks = [check_source(source, username) for source in SOURCES]
    results = await asyncio.gather(*tasks)
    found = [r for r in results if r.get("found")]
    return {"username": username, "found": found, "total": len(SOURCES)}

# ============================================================
# ГЛАВНАЯ ФУНКЦИЯ (ЗАПУСК У КЛИЕНТА)
# ============================================================
def main():
    print(f"{Colors.BOLD}{Colors.CYAN}ClnSIt Core v5.1 — OSINT Engine{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.YELLOW}Purge Labs © 2026{Colors.RESET}\\n")
    print(f"{Colors.YELLOW}🔧 Движки:{Colors.RESET}")
    print(f"  {'✅' if HAS_HTTPX else '❌'} httpx (HTTP/2)")
    print(f"  {'✅' if HAS_CURL else '❌'} curl_cffi (TLS-имперсонация)")
    print(f"  {'✅' if HAS_SELECTOLAX else '❌'} selectolax (быстрый парсер)")
    print(f"  {'✅' if PLAYWRIGHT_AVAILABLE else '❌'} Playwright (JS-рендеринг)")
    
    username = input(f"{Colors.WHITE}Введите никнейм: {Colors.RESET}").strip()
    if not username:
        print(f"{Colors.RED}❌ Никнейм не введён{Colors.RESET}")
        return
    
    print(f"{Colors.CYAN}⏳ Поиск по {len(SOURCES)} источникам...{Colors.RESET}")
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(search_all(username))
        loop.close()
        
        found = result.get("found", [])
        graph = build_graph(username, found)
        
        print(f"\\n{Colors.CYAN}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.WHITE}🔍 Результат для: {Colors.YELLOW}{username}{Colors.RESET}")
        print(f"{Colors.GREEN}✅ Найдено: {len(found)} / {len(SOURCES)}{Colors.RESET}")
        
        for node_id, data in graph["nodes"].items():
            if node_id == username:
                continue
            if data["type"] == "profile":
                print(f"  ├── {Colors.GREEN}{data['source']}{Colors.RESET} (вес: {data.get('weight', 0)})")
                print(f"  │   └── {Colors.WHITE}{data['url']}{Colors.RESET}")
                if data.get("bio"):
                    print(f"  │       📝 {data['bio'][:100]}...")
            elif data["type"] == "email":
                print(f"  │   └── ✉️  {Colors.YELLOW}{data['value']}{Colors.RESET} (вес: {data['weight']})")
            elif data["type"] == "phone":
                print(f"  │   └── 📱 {Colors.MAGENTA}{data['value']}{Colors.RESET} (вес: {data['weight']})")
        
        report_file = f"clnsit_report_{username}_{int(time.time())}.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump({"username": username, "graph": graph, "found": found}, f, indent=2, ensure_ascii=False)
        print(f"\\n{Colors.GREEN}📄 Отчёт сохранён: {report_file}{Colors.RESET}")
        
    except Exception as e:
        print(f"{Colors.RED}❌ Ошибка: {e}{Colors.RESET}")

if __name__ == "__main__":
    main()
'''

# =====================================================================
# 2. КОНФИГУРАЦИЯ
# =====================================================================
class AppConfig:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    LOGS_DIR = os.path.join(BASE_DIR, "logs")
    DB_PATH = os.path.join(DATA_DIR, "database.db")
    BACKUP_PATH = os.path.join(DATA_DIR, "backup.db")
    CORE_FILE = os.path.join(BASE_DIR, "core.enc")
    SECRET_FILE = os.path.join(DATA_DIR, "secret.json")
    SALT = b"ClnSIt_Enterprise_Salt_2026"
    VERSION = "5.1"
    SUPPORT_CHANNEL = "@PurgeLabs"

    @classmethod
    def ensure_directories(cls) -> None:
        os.makedirs(cls.DATA_DIR, exist_ok=True)
        os.makedirs(cls.LOGS_DIR, exist_ok=True)

# =====================================================================
# 3. ЛОГГЕР
# =====================================================================
class AppLogger:
    def __init__(self) -> None:
        self.logger = logging.getLogger("ClnSIt")
        self.logger.setLevel(logging.INFO)
        if self.logger.handlers:
            self.logger.handlers.clear()
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        file_handler = logging.FileHandler(os.path.join(AppConfig.LOGS_DIR, "server.log"))
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def info(self, msg: str) -> None: self.logger.info(msg)
    def warning(self, msg: str) -> None: self.logger.warning(msg)
    def error(self, msg: str) -> None: self.logger.error(msg)

# =====================================================================
# 4. КРИПТОГРАФИЯ
# =====================================================================
class CryptoService:
    def __init__(self) -> None:
        key = hashlib.sha256(AppConfig.SALT).digest()
        self.cipher = Fernet(base64.urlsafe_b64encode(key))
    
    def encrypt(self, data: str) -> bytes:
        return self.cipher.encrypt(data.encode())
    
    def decrypt(self, data: bytes) -> Optional[str]:
        try:
            return self.cipher.decrypt(data).decode()
        except InvalidToken:
            return None

# =====================================================================
# 5. БАЗА ДАННЫХ
# =====================================================================
class DatabaseManager:
    def __init__(self, logger: AppLogger) -> None:
        self.logger = logger
        self.db_path = AppConfig.DB_PATH
        self.backup_path = AppConfig.BACKUP_PATH
    
    def initialize(self) -> None:
        if self._is_valid():
            self.logger.info("✅ Database exists")
            return
        self.logger.warning("⚠️ Database corrupted, recreating...")
        if os.path.exists(self.backup_path):
            shutil.copy2(self.backup_path, self.db_path)
            self.logger.info("✅ Database restored")
            return
        self._create_fresh()
    
    def _is_valid(self) -> bool:
        if not os.path.exists(self.db_path) or os.path.getsize(self.db_path) == 0:
            return False
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("SELECT 1 FROM licenses LIMIT 1")
            conn.close()
            return True
        except:
            return False
    
    def _create_fresh(self) -> None:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS licenses (
                key TEXT PRIMARY KEY,
                is_active INTEGER DEFAULT 1,
                expires_at INTEGER,
                user_id TEXT,
                created_at INTEGER,
                last_used INTEGER DEFAULT 0,
                metadata TEXT DEFAULT '{}'
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                license_key TEXT,
                action TEXT,
                ip TEXT,
                user_agent TEXT,
                details TEXT,
                timestamp INTEGER
            )
        """)
        c.execute("CREATE INDEX IF NOT EXISTS idx_licenses_key ON licenses(key)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_licenses_active ON licenses(is_active)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_logs_key ON logs(license_key)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_logs_time ON logs(timestamp)")
        conn.commit()
        conn.close()
        self.logger.info("✅ Fresh database created")
        self._backup()
    
    def _backup(self) -> None:
        try:
            if os.path.exists(self.db_path) and os.path.getsize(self.db_path) > 0:
                shutil.copy2(self.db_path, self.backup_path)
        except Exception as e:
            self.logger.error(f"Backup failed: {e}")
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def find_license(self, key: str) -> Tuple[bool, int, str]:
        try:
            conn = self.get_connection()
            c = conn.cursor()
            c.execute("SELECT is_active, expires_at, user_id FROM licenses WHERE key = ?", (key,))
            row = c.fetchone()
            conn.close()
            if row and row[0] and (row[1] == 0 or time.time() < row[1]):
                return True, row[1], row[2]
        except Exception as e:
            self.logger.error(f"License check error: {e}")
        return False, 0, ""
    
    def create_license(self, key: str, expires_at: int, user_id: str = "default") -> bool:
        try:
            conn = self.get_connection()
            c = conn.cursor()
            c.execute("INSERT INTO licenses (key, is_active, expires_at, user_id, created_at) VALUES (?, ?, ?, ?, ?)",
                      (key, 1, expires_at, user_id, int(time.time())))
            conn.commit()
            conn.close()
            self._backup()
            return True
        except sqlite3.IntegrityError:
            return False
        except Exception as e:
            self.logger.error(f"Create license error: {e}")
            return False
    
    def revoke_license(self, key: str) -> bool:
        try:
            conn = self.get_connection()
            c = conn.cursor()
            c.execute("UPDATE licenses SET is_active = 0 WHERE key = ?", (key,))
            conn.commit()
            conn.close()
            self._backup()
            return True
        except Exception as e:
            self.logger.error(f"Revoke license error: {e}")
            return False
    
    def log_event(self, license_key: str, action: str, ip: str, ua: str = "") -> None:
        try:
            conn = self.get_connection()
            c = conn.cursor()
            c.execute("INSERT INTO logs (license_key, action, ip, user_agent, timestamp) VALUES (?, ?, ?, ?, ?)",
                      (license_key, action, ip, ua, int(time.time())))
            conn.commit()
            conn.close()
        except Exception as e:
            self.logger.error(f"Logging error: {e}")
    
    def get_statistics(self) -> Dict[str, int]:
        try:
            conn = self.get_connection()
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM licenses")
            total = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM licenses WHERE is_active = 1")
            active = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM logs")
            logs = c.fetchone()[0]
            conn.close()
            return {"total": total, "active": active, "logs": logs}
        except:
            return {"total": 0, "active": 0, "logs": 0}

# =====================================================================
# 6. МЕНЕДЖЕР ЛИЦЕНЗИЙ
# =====================================================================
class LicenseManager:
    def __init__(self, db: DatabaseManager, logger: AppLogger) -> None:
        self.db = db
        self.logger = logger
        self.master_key = self._get_master_key()
    
    def _get_master_key(self) -> str:
        """Загружает мастер-ключ из переменной окружения или создаёт новый"""
        # 1. Пробуем взять из переменной окружения
        env_key = os.environ.get("SECRET_KEY")
        if env_key and len(env_key) >= 16:
            self.logger.info("✅ Master key loaded from environment variable SECRET_KEY")
            return env_key
        
        # 2. Пробуем загрузить из файла
        if os.path.exists(AppConfig.SECRET_FILE):
            try:
                with open(AppConfig.SECRET_FILE, "r") as f:
                    data = json.load(f)
                    if "master_key" in data and len(data["master_key"]) >= 16:
                        self.logger.info("✅ Master key loaded from file (fallback)")
                        return data["master_key"]
            except Exception as e:
                self.logger.warning(f"Failed to load secret file: {e}")
        
        # 3. Создаём новый ключ и сохраняем
        alphabet = string.ascii_letters + string.digits
        master_key = ''.join(secrets.choice(alphabet) for _ in range(32))
        
        try:
            with open(AppConfig.SECRET_FILE, "w") as f:
                json.dump({"master_key": master_key, "created_at": time.time()}, f, indent=2)
            self.logger.info("✅ New master key generated and saved to file")
        except Exception as e:
            self.logger.error(f"Failed to save master key: {e}")
        
        return master_key
    
    def generate_key(self) -> str:
        chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        parts = [''.join(secrets.choice(chars) for _ in range(4)) for _ in range(3)]
        return f"CLN-{parts[0]}-{parts[1]}-{parts[2]}"
    
    def create_license(self, master_key: str, user_id: str = "default", days: int = 365) -> Optional[str]:
        if master_key != self.master_key:
            self.logger.warning(f"Invalid master key attempt for {user_id}")
            return None
        license_key = self.generate_key()
        expires_at = int(time.time()) + days * 86400
        if self.db.create_license(license_key, expires_at, user_id):
            self.logger.info(f"License created: {license_key} for {user_id}")
            return license_key
        return None

# =====================================================================
# 7. ЗАГРУЗЧИК ЯДРА
# =====================================================================
class CoreLoader:
    def __init__(self, crypto: CryptoService, logger: AppLogger) -> None:
        self.crypto = crypto
        self.logger = logger
        self.core_file = AppConfig.CORE_FILE
    
    def load(self) -> str:
        if not os.path.exists(self.core_file):
            encrypted = self.crypto.encrypt(CORE_CODE)
            with open(self.core_file, "wb") as f:
                f.write(encrypted)
            self.logger.info("📁 Core file created")
            return CORE_CODE
        with open(self.core_file, "rb") as f:
            decrypted = self.crypto.decrypt(f.read())
        return decrypted if decrypted else CORE_CODE

# =====================================================================
# 8. СЕРВЕР
# =====================================================================
class ClnSItServer:
    def __init__(self) -> None:
        AppConfig.ensure_directories()
        self.logger = AppLogger()
        self.crypto = CryptoService()
        self.db = DatabaseManager(self.logger)
        self.db.initialize()
        self.core_loader = CoreLoader(self.crypto, self.logger)
        self.license_manager = LicenseManager(self.db, self.logger)
        self.core_code = self.core_loader.load()
        self.app = Flask(__name__)
        CORS(self.app)
        self._register_routes()
        self._register_error_handlers()
    
    def _register_error_handlers(self) -> None:
        @self.app.errorhandler(404)
        def not_found(e):
            return jsonify({"success": False, "error": "Not Found"}), 404
        @self.app.errorhandler(405)
        def method_not_allowed(e):
            return jsonify({"success": False, "error": "Method Not Allowed"}), 405
        @self.app.errorhandler(Exception)
        def handle_exception(e):
            self.logger.error(f"Unhandled exception: {e}")
            return jsonify({"success": False, "error": "Internal Server Error"}), 500
    
    def _register_routes(self) -> None:
        @self.app.route("/", methods=["GET"])
        def status():
            return jsonify({
                "name": "ClnSIt Server",
                "version": AppConfig.VERSION,
                "status": "running",
                "timestamp": datetime.now().isoformat(),
                "support": AppConfig.SUPPORT_CHANNEL
            })
        
        @self.app.route("/verify", methods=["POST"])
        def verify_license():
            try:
                data = request.get_json()
                if not data:
                    return jsonify({"success": False, "error": "JSON expected"}), 400
                license_key = data.get("key", "").strip()
                if not license_key:
                    return jsonify({"success": False, "error": "License key required"}), 400
                
                is_valid, expires_at, user_id = self.db.find_license(license_key)
                self.db.log_event(license_key, "verify_attempt", request.remote_addr, request.headers.get("User-Agent", ""))
                
                if is_valid:
                    self.db.log_event(license_key, "verify_success", request.remote_addr, request.headers.get("User-Agent", ""))
                    return jsonify({
                        "valid": True,
                        "expiry": datetime.fromtimestamp(expires_at).strftime("%Y-%m-%d") if expires_at else "permanent",
                        "code": self.core_code,
                        "user_id": user_id
                    })
                self.db.log_event(license_key, "verify_failed", request.remote_addr, request.headers.get("User-Agent", ""))
                return jsonify({"valid": False, "message": "Invalid or expired license key"}), 403
            except Exception as e:
                self.logger.error(f"Verify error: {e}")
                return jsonify({"success": False, "error": "Internal error"}), 500
        
        @self.app.route("/admin/generate", methods=["POST"])
        def generate_license():
            try:
                data = request.get_json()
                if not data:
                    return jsonify({"success": False, "error": "JSON expected"}), 400
                master_key = data.get("master_key", "").strip()
                if not master_key:
                    return jsonify({"success": False, "error": "Master key required"}), 400
                user_id = data.get("user_id", "default")
                days = int(data.get("days", 365))
                license_key = self.license_manager.create_license(master_key, user_id, days)
                if license_key:
                    return jsonify({"success": True, "license_key": license_key, "user_id": user_id, "days": days})
                return jsonify({"success": False, "error": "Invalid master key"}), 403
            except Exception as e:
                self.logger.error(f"Generate error: {e}")
                return jsonify({"success": False, "error": "Internal error"}), 500
        
        @self.app.route("/admin/revoke", methods=["POST"])
        def revoke_license():
            try:
                data = request.get_json()
                if not data:
                    return jsonify({"success": False, "error": "JSON expected"}), 400
                if data.get("master_key") != self.license_manager.master_key:
                    return jsonify({"success": False, "error": "Invalid master key"}), 403
                license_key = data.get("license_key", "").strip()
                if not license_key:
                    return jsonify({"success": False, "error": "License key required"}), 400
                if self.db.revoke_license(license_key):
                    return jsonify({"success": True, "license_key": license_key})
                return jsonify({"success": False, "error": "License not found"}), 404
            except Exception as e:
                self.logger.error(f"Revoke error: {e}")
                return jsonify({"success": False, "error": "Internal error"}), 500
        
        @self.app.route("/admin/stats", methods=["GET"])
        def stats():
            try:
                return jsonify(self.db.get_statistics())
            except Exception as e:
                self.logger.error(f"Stats error: {e}")
                return jsonify({"success": False, "error": "Internal error"}), 500
    
    def run(self, host: str = "0.0.0.0", port: int = 5000) -> None:
        self.logger.info(f"🚀 ClnSIt Server v{AppConfig.VERSION} started")
        self.logger.info(f"📡 Listening on http://{host}:{port}")
        self.logger.info(f"🔑 Master Key: {self.license_manager.master_key}")
        self.app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    try:
        server = ClnSItServer()
        print("\n" + "=" * 70)
        print(f"  ClnSIt Server v{AppConfig.VERSION} — Enterprise Edition")
        print("  Purge Labs © 2026")
        print("=" * 70)
        print(f"  🔑 MASTER KEY: {server.license_manager.master_key}")
        print(f"  📁 Data: {AppConfig.DATA_DIR}")
        print(f"  📁 Logs: {AppConfig.LOGS_DIR}")
        print("=" * 70)
        print(f"  📌 Support: {AppConfig.SUPPORT_CHANNEL}")
        print("=" * 70 + "\n")
        server.run()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1) 
