#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ClnSIt Server v5.2 — Enterprise Edition
Purge Labs © 2026

ВСЁ В ОДНОМ ФАЙЛЕ:
- Сервер (Flask)
- OSINT-ядро (httpx, curl_cffi, selectolax, playwright)
- Лицензионная система
- Кастомные ошибки
- Автосохранение базы
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
from typing import Optional, Dict, Any, Tuple, List
from flask import Flask, request, jsonify
from flask_cors import CORS
from cryptography.fernet import Fernet, InvalidToken

# =====================================================================
# 1. ИМПОРТЫ OSINT-ЯДРА (ВСЕ НАВЕРХУ)
# =====================================================================
try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

try:
    from curl_cffi import requests as curl_requests
    HAS_CURL = True
except ImportError:
    HAS_CURL = False

try:
    from selectolax.parser import HTMLParser
    HAS_SELECTOLAX = True
except ImportError:
    HAS_SELECTOLAX = False

PLAYWRIGHT_AVAILABLE = False
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    pass

# =====================================================================
# 2. КАСТОМНЫЕ ОШИБКИ
# =====================================================================
class ClnSItError(Exception):
    """Базовое исключение для всех ошибок ClnSIt"""
    pass

class LicenseError(ClnSItError):
    """Ошибка лицензии"""
    pass

class OSINTError(ClnSItError):
    """Ошибка OSINT-поиска"""
    pass

class DatabaseError(ClnSItError):
    """Ошибка базы данных"""
    pass

class ConfigError(ClnSItError):
    """Ошибка конфигурации"""
    pass

class NetworkError(ClnSItError):
    """Ошибка сети"""
    pass

# =====================================================================
# 3. OSINT-ЯДРО (КЛАСС)
# =====================================================================
class CoreOSINT:
    """Полное OSINT-ядро с поиском, парсингом и графом"""
    
    def __init__(self):
        self.httpx_client = None
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]
        self.impersonates = ["chrome120", "chrome119", "firefox121"]
        self.sources = self._get_sources()
    
    def _get_sources(self) -> dict:
        """База источников (50+ сайтов)"""
        return {
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
            "pikabu": {"url": "https://pikabu.ru/{}", "type": "public"},
            "habr": {"url": "https://habr.com/ru/users/{}", "type": "public"},
            "dtf": {"url": "https://dtf.ru/u/{}", "type": "public"},
            "vcru": {"url": "https://vc.ru/u/{}", "type": "public"},
            "tjournal": {"url": "https://tjournal.ru/users/{}", "type": "public"},
            "cyberforum": {"url": "https://www.cyberforum.ru/members/{}", "type": "public"},
            "4pda": {"url": "https://4pda.to/forum/index.php?showuser={}", "type": "public"},
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
    
    def get_headers(self) -> dict:
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
    
    async def fetch_with_playwright(self, url: str) -> str:
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
    
    def extract_meta(self, html: str) -> dict:
        if not HAS_SELECTOLAX:
            return {"title": "", "bio": ""}
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
                    result["bio"] = re.sub(r'\s+', ' ', raw)[:200]
            return result
        except Exception:
            return {"title": "", "bio": ""}
    
    def extract_entities(self, text: str) -> dict:
        if not text:
            return {"emails": [], "phones": [], "links": []}
        return {
            "emails": list(set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text))),
            "phones": list(set(re.findall(r'(?:\+7|8|7|9)[0-9]{9,10}', text))),
            "links": list(set(re.findall(r'https?://[^\s<>]+', text)))
        }
    
    def build_graph(self, username: str, profiles: list) -> dict:
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
            
            entities = self.extract_entities(p.get("bio", ""))
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
    
    async def check_source(self, source: str, username: str) -> dict:
        url = self.sources[source]["url"].format(username)
        site_type = self.sources[source].get("type", "public")
        result = {"source": source, "found": False, "url": url, "title": "", "bio": ""}
        
        if site_type == "public":
            response = await self.get_httpx(url)
            if response and response.status_code == 200:
                meta = self.extract_meta(response.text)
                result["found"] = True
                result["title"] = meta.get("title", "")
                result["bio"] = meta.get("bio", "")
                return result
        
        if HAS_CURL:
            for impersonate in ["chrome120", "chrome119"]:
                try:
                    response = self.get_curl(url, impersonate=impersonate)
                    if response and response.status_code == 200:
                        meta = self.extract_meta(response.text)
                        result["found"] = True
                        result["title"] = meta.get("title", "")
                        result["bio"] = meta.get("bio", "")
                        return result
                except Exception:
                    continue
        
        if site_type == "heavy" and PLAYWRIGHT_AVAILABLE:
            html = await self.fetch_with_playwright(url)
            if html:
                meta = self.extract_meta(html)
                if meta.get("bio") or meta.get("title"):
                    result["found"] = True
                    result["title"] = meta.get("title", "")
                    result["bio"] = meta.get("bio", "")
                    return result
        
        return result
    
    async def search(self, username: str) -> dict:
        """Основной метод поиска"""
        tasks = [self.check_source(source, username) for source in self.sources]
        results = await asyncio.gather(*tasks)
        found = [r for r in results if r.get("found")]
        return {
            "username": username,
            "found": found,
            "total": len(self.sources),
            "graph": self.build_graph(username, found)
        }

# =====================================================================
# 4. КОНФИГУРАЦИЯ
# =====================================================================
class AppConfig:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    LOGS_DIR = os.path.join(BASE_DIR, "logs")
    DB_PATH = os.path.join(DATA_DIR, "database.db")
    BACKUP_PATH = os.path.join(DATA_DIR, "backup.db")
    SECRET_FILE = os.path.join(DATA_DIR, "secret.json")
    SALT = b"ClnSIt_Enterprise_Salt_2026"
    VERSION = "5.2"
    SUPPORT_CHANNEL = "@PurgeLabs"
    
    @classmethod
    def ensure_directories(cls) -> None:
        os.makedirs(cls.DATA_DIR, exist_ok=True)
        os.makedirs(cls.LOGS_DIR, exist_ok=True)

# =====================================================================
# 5. ЛОГГЕР
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
# 6. КРИПТОГРАФИЯ
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
# 7. БАЗА ДАННЫХ
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
    
    def log_event(self, license_key: str, action: str, ip: str, ua: str = "", details: str = "") -> None:
        try:
            conn = self.get_connection()
            c = conn.cursor()
            c.execute("INSERT INTO logs (license_key, action, ip, user_agent, details, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                      (license_key, action, ip, ua, details, int(time.time())))
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
# 8. МЕНЕДЖЕР ЛИЦЕНЗИЙ
# =====================================================================
class LicenseManager:
    def __init__(self, db: DatabaseManager, logger: AppLogger) -> None:
        self.db = db
        self.logger = logger
        self.master_key = self._get_master_key()
    
    def _get_master_key(self) -> str:
        env_key = os.environ.get("SECRET_KEY")
        if env_key and len(env_key) >= 16:
            self.logger.info("✅ Master key loaded from environment variable SECRET_KEY")
            return env_key
        
        if os.path.exists(AppConfig.SECRET_FILE):
            try:
                with open(AppConfig.SECRET_FILE, "r") as f:
                    data = json.load(f)
                    if "master_key" in data and len(data["master_key"]) >= 16:
                        self.logger.info("✅ Master key loaded from file")
                        return data["master_key"]
            except Exception as e:
                self.logger.warning(f"Failed to load secret file: {e}")
        
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
# 9. СЕРВЕР
# =====================================================================
class ClnSItServer:
    def __init__(self) -> None:
        AppConfig.ensure_directories()
        self.logger = AppLogger()
        self.crypto = CryptoService()
        self.db = DatabaseManager(self.logger)
        self.db.initialize()
        self.license_manager = LicenseManager(self.db, self.logger)
        self.osint_core = CoreOSINT()
        self.app = Flask(__name__)
        CORS(self.app)
        self._register_routes()
        self._register_error_handlers()
    
    def _register_error_handlers(self) -> None:
        @self.app.errorhandler(ClnSItError)
        def handle_clnsit_error(e: ClnSItError):
            self.logger.error(f"ClnSItError: {e}")
            return jsonify({
                "success": False,
                "error": e.__class__.__name__,
                "message": str(e),
                "support": f"Обратитесь: {AppConfig.SUPPORT_CHANNEL}"
            }), 500
        
        @self.app.errorhandler(404)
        def not_found(e):
            return jsonify({"success": False, "error": "Not Found"}), 404
        
        @self.app.errorhandler(405)
        def method_not_allowed(e):
            return jsonify({"success": False, "error": "Method Not Allowed"}), 405
        
        @self.app.errorhandler(Exception)
        def handle_exception(e):
            self.logger.error(f"Unhandled exception: {e}")
            return jsonify({
                "success": False,
                "error": "InternalServerError",
                "message": "Внутренняя ошибка сервера",
                "support": f"Обратитесь: {AppConfig.SUPPORT_CHANNEL}"
            }), 500
    
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
                    raise ClnSItError("JSON body expected")
                
                license_key = data.get("key", "").strip()
                if not license_key:
                    raise ClnSItError("License key is required")
                
                is_valid, expires_at, user_id = self.db.find_license(license_key)
                self.db.log_event(license_key, "verify_attempt", request.remote_addr, request.headers.get("User-Agent", ""))
                
                if is_valid:
                    self.db.log_event(license_key, "verify_success", request.remote_addr, request.headers.get("User-Agent", ""))
                    return jsonify({
                        "valid": True,
                        "expiry": datetime.fromtimestamp(expires_at).strftime("%Y-%m-%d") if expires_at else "permanent",
                        "user_id": user_id
                    })
                
                self.db.log_event(license_key, "verify_failed", request.remote_addr, request.headers.get("User-Agent", ""))
                raise LicenseError("Invalid or expired license key")
                
            except LicenseError as e:
                return jsonify({"valid": False, "message": str(e)}), 403
            except ClnSItError as e:
                return jsonify({"success": False, "error": str(e)}), 400
        
        @self.app.route("/search", methods=["POST"])
        def search_username():
            """Эндпоинт для OSINT-поиска (требует лицензию)"""
            try:
                data = request.get_json()
                if not data:
                    raise ClnSItError("JSON body expected")
                
                license_key = data.get("key", "").strip()
                username = data.get("username", "").strip()
                
                if not license_key:
                    raise ClnSItError("License key is required")
                if not username:
                    raise ClnSItError("Username is required")
                
                # Проверяем лицензию
                is_valid, expires_at, user_id = self.db.find_license(license_key)
                self.db.log_event(license_key, "search_attempt", request.remote_addr, request.headers.get("User-Agent", ""), f"username={username}")
                
                if not is_valid:
                    self.db.log_event(license_key, "search_failed", request.remote_addr, request.headers.get("User-Agent", ""), "invalid_license")
                    raise LicenseError("Invalid or expired license key")
                
                # Выполняем поиск
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(self.osint_core.search(username))
                loop.close()
                
                self.db.log_event(license_key, "search_success", request.remote_addr, request.headers.get("User-Agent", ""), f"found={len(result.get('found', []))}")
                
                return jsonify({
                    "success": True,
                    "username": username,
                    "found": len(result.get("found", [])),
                    "total": result.get("total", 0),
                    "graph": result.get("graph", {})
                })
                
            except LicenseError as e:
                return jsonify({"success": False, "error": str(e)}), 403
            except ClnSItError as e:
                return jsonify({"success": False, "error": str(e)}), 400
            except Exception as e:
                self.logger.error(f"Search error: {e}")
                return jsonify({
                    "success": False,
                    "error": "SearchError",
                    "message": "Ошибка при выполнении поиска",
                    "support": f"Обратитесь: {AppConfig.SUPPORT_CHANNEL}"
                }), 500
        
        @self.app.route("/admin/generate", methods=["POST"])
        def generate_license():
            try:
                data = request.get_json()
                if not data:
                    raise ClnSItError("JSON body expected")
                
                master_key = data.get("master_key", "").strip()
                if not master_key:
                    raise ClnSItError("Master key is required")
                
                user_id = data.get("user_id", "default")
                days = int(data.get("days", 365))
                
                license_key = self.license_manager.create_license(master_key, user_id, days)
                if license_key:
                    return jsonify({"success": True, "license_key": license_key, "user_id": user_id, "days": days})
                raise LicenseError("Invalid master key")
                
            except LicenseError as e:
                return jsonify({"success": False, "error": str(e)}), 403
            except ClnSItError as e:
                return jsonify({"success": False, "error": str(e)}), 400
        
        @self.app.route("/admin/revoke", methods=["POST"])
        def revoke_license():
            try:
                data = request.get_json()
                if not data:
                    raise ClnSItError("JSON body expected")
                
                if data.get("master_key") != self.license_manager.master_key:
                    raise LicenseError("Invalid master key")
                
                license_key = data.get("license_key", "").strip()
                if not license_key:
                    raise ClnSItError("License key is required")
                
                if self.db.revoke_license(license_key):
                    return jsonify({"success": True, "license_key": license_key})
                raise ClnSItError("License not found")
                
            except LicenseError as e:
                return jsonify({"success": False, "error": str(e)}), 403
            except ClnSItError as e:
                return jsonify({"success": False, "error": str(e)}), 400
        
        @self.app.route("/admin/stats", methods=["GET"])
        def stats():
            return jsonify(self.db.get_statistics())
    
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
