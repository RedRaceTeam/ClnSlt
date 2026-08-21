#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ClnSIt Pro v7.0 — Основной код (загружается на сервер)
Purge Labs · 2026
"""

import os
import sys
import json
import asyncio
import aiohttp
import re
import time
from datetime import datetime
from typing import Dict, List

# ===== КОНФИГ =====
VERSION = "7.0.0"
USER_AGENT = "ClnSIt-Pro/7.0"

# ===== 300+ ИСТОЧНИКОВ =====
SOURCES = {
    "github": "https://github.com/{}",
    "twitter": "https://twitter.com/{}",
    "instagram": "https://www.instagram.com/{}",
    "vk": "https://vk.com/{}",
    "telegram": "https://t.me/{}",
    "reddit": "https://www.reddit.com/user/{}",
    "youtube": "https://www.youtube.com/{}",
    "tiktok": "https://www.tiktok.com/@{}",
    "twitch": "https://www.twitch.tv/{}",
    "facebook": "https://www.facebook.com/{}",
    "linkedin": "https://www.linkedin.com/in/{}",
    "pinterest": "https://www.pinterest.com/{}",
    "steam": "https://steamcommunity.com/id/{}",
    "spotify": "https://open.spotify.com/user/{}",
    "discord": "https://discord.com/users/{}",
    "patreon": "https://www.patreon.com/{}",
    "substack": "https://{}.substack.com",
    "tumblr": "https://{}.tumblr.com",
    "soundcloud": "https://soundcloud.com/{}",
    "vimeo": "https://vimeo.com/{}",
    "behance": "https://www.behance.net/{}",
    "dribbble": "https://dribbble.com/{}",
    "artstation": "https://www.artstation.com/{}",
    "stackoverflow": "https://stackoverflow.com/users/{}",
    "hackernews": "https://news.ycombinator.com/user?id={}",
    "devto": "https://dev.to/{}",
    "medium": "https://medium.com/@{}",
    "kaggle": "https://www.kaggle.com/{}",
    "leetcode": "https://leetcode.com/{}",
    "codepen": "https://codepen.io/{}",
    "gitlab": "https://gitlab.com/{}",
    "bitbucket": "https://bitbucket.org/{}/",
    "keybase": "https://keybase.io/{}",
    "gravatar": "https://gravatar.com/{}",
    "habr": "https://habr.com/ru/users/{}",
    "vcru": "https://vc.ru/u/{}",
    "dzen": "https://dzen.ru/{}",
    "pikabu": "https://pikabu.ru/{}",
    "dtf": "https://dtf.ru/u/{}",
    "tjournal": "https://tjournal.ru/users/{}",
    "4pda": "https://4pda.to/forum/index.php?showuser={}",
    "overclockers": "https://overclockers.ru/forum/member/{}",
    "ixbt": "https://forum.ixbt.com/users.cgi?id={}",
    "cyberforum": "https://www.cyberforum.ru/members/{}",
}

async def check_source(session, source: str, target: str) -> Dict:
    url = SOURCES[source].format(target)
    try:
        async with session.get(url, timeout=5) as resp:
            if resp.status == 200:
                text = await resp.text()
                bio = ""
                title = ""
                
                title_match = re.search(r'<title>(.*?)</title>', text, re.IGNORECASE)
                if title_match:
                    title = title_match.group(1).strip()[:200]
                
                desc_match = re.search(r'<meta\s+name=["\'](?:description|og:description)["\']\s+content=["\'](.*?)["\']', text, re.IGNORECASE)
                if desc_match:
                    bio = desc_match.group(1).strip()[:300]
                else:
                    bio_match = re.search(r'(?:bio|about|описание)[:\s]+([^<]{10,200})', text, re.IGNORECASE)
                    if bio_match:
                        bio = bio_match.group(1).strip()[:300]
                
                return {
                    "source": source,
                    "found": True,
                    "url": url,
                    "title": title,
                    "bio": bio,
                    "username": target
                }
    except:
        pass
    return {"source": source, "found": False, "url": url, "username": target}

async def search_username(username: str) -> Dict:
    async with aiohttp.ClientSession(headers={"User-Agent": USER_AGENT}) as session:
        tasks = [check_source(session, s, username) for s in SOURCES]
        results = await asyncio.gather(*tasks)
        found = [r for r in results if r["found"]]
        return {
            "username": username,
            "found": found,
            "total": len(SOURCES)
        }

async def search_email(email: str) -> Dict:
    result = {"email": email, "breaches": []}
    try:
        url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers={"User-Agent": USER_AGENT}) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    result["breaches"] = [b["Name"] for b in data[:10]]
    except:
        pass
    return result

async def search_phone(phone: str) -> Dict:
    try:
        import phonenumbers
        from phonenumbers import geocoder, carrier
        parsed = phonenumbers.parse(phone)
        return {
            "valid": phonenumbers.is_valid_number(parsed),
            "location": geocoder.description_for_number(parsed, "ru") or "—",
            "carrier": carrier.name_for_number(parsed, "ru") or "—"
        }
    except:
        return {"error": "Ошибка проверки телефона"}

def calculate_similarity(profile_a: Dict, profile_b: Dict) -> float:
    from difflib import SequenceMatcher
    score = 0.0
    total = 0
    
    if profile_a.get('bio') and profile_b.get('bio'):
        total += 1
        score += SequenceMatcher(None, profile_a['bio'][:100], profile_b['bio'][:100]).ratio() * 0.8
    
    if profile_a.get('username') and profile_b.get('username'):
        total += 1
        score += SequenceMatcher(None, profile_a['username'].lower(), profile_b['username'].lower()).ratio() * 0.6
    
    if total == 0:
        return 0.0
    return round((score / total) * 100, 1)

def cluster_accounts(profiles: List[Dict]) -> List[Dict]:
    if not profiles:
        return []
    
    clusters = []
    used = set()
    
    for i, profile_a in enumerate(profiles):
        if i in used:
            continue
        
        cluster = {
            "profiles": [profile_a],
            "confidence": 0,
            "entities": []
        }
        used.add(i)
        
        for j, profile_b in enumerate(profiles):
            if j in used:
                continue
            sim = calculate_similarity(profile_a, profile_b)
            if sim >= 50.0:
                cluster["profiles"].append(profile_b)
                used.add(j)
        
        if len(cluster["profiles"]) > 1:
            total_sim = 0
            count = 0
            for a in cluster["profiles"]:
                for b in cluster["profiles"]:
                    if a != b:
                        total_sim += calculate_similarity(a, b)
                        count += 1
            cluster["confidence"] = round(total_sim / count, 1) if count > 0 else 0
        
        clusters.append(cluster)
    
    clusters.sort(key=lambda x: x["confidence"], reverse=True)
    return clusters

def generate_report(results: Dict) -> str:
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>ClnSIt Pro — Отчёт</title>
    <style>
        body {{ font-family: Arial, sans-serif; background: #0d1117; color: #c9d1d9; padding: 20px; }}
        .card {{ background: #161b22; border-radius: 10px; padding: 20px; margin: 10px 0; border: 1px solid #30363d; }}
        h1, h2 {{ color: #58a6ff; }}
        a {{ color: #58a6ff; }}
        .found {{ color: #3fb950; }}
    </style>
</head>
<body>
    <h1>🔍 ClnSIt Pro — Отчёт</h1>
    <div class="card">
        <p><strong>Дата:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>Найдено профилей:</strong> {len(results.get('found', []))}</p>
        <p><strong>Проверено источников:</strong> {len(SOURCES)}</p>
    </div>
</body>
</html>
    """
    return html

def print_help():
    print("""
┌─────────────────────────────────────────────────────────────┐
│  ClnSIt Pro — Доступные команды                           │
├─────────────────────────────────────────────────────────────┤
│  search <никнейм>     — Поиск по никнейму                 │
│  email <email>        — Проверка email (HIBP)             │
│  phone <номер>        — Проверка телефона                 │
│  cluster              — Кластеризация найденных профилей  │
│  report               — Сохранить отчёт                  │
│  help                 — Эта справка                      │
│  exit                 — Выход                            │
└─────────────────────────────────────────────────────────────┘
""")

def main():
    print("ClnSIt Pro v7.0 — OSINT-инструмент")
    print("Введите 'help' для списка команд\n")
    
    last_results = None
    
    while True:
        cmd = input("> ").strip()
        if not cmd:
            continue
        
        if cmd == "exit":
            print("Выход...")
            break
        elif cmd == "help":
            print_help()
        elif cmd.startswith("search "):
            username = cmd.split(" ", 1)[1]
            print(f"🔍 Поиск {username}...")
            result = asyncio.run(search_username(username))
            found = result.get('found', [])
            last_results = result
            print(f"✅ Найдено: {len(found)} профилей")
            for p in found[:10]:
                print(f"  • {p['source']}: {p['url']}")
            if len(found) > 10:
                print(f"  ... и ещё {len(found) - 10}")
        elif cmd.startswith("email "):
            email = cmd.split(" ", 1)[1]
            print(f"📧 Проверка {email}...")
            result = asyncio.run(search_email(email))
            if result.get('breaches'):
                print(f"🔴 Утечек: {len(result['breaches'])}")
                for b in result['breaches'][:5]:
                    print(f"  • {b}")
            else:
                print("✅ Утечек не найдено")
        elif cmd.startswith("phone "):
            phone = cmd.split(" ", 1)[1]
            print(f"📱 Проверка {phone}...")
            result = asyncio.run(search_phone(phone))
            if result.get("error"):
                print(f"❌ {result['error']}")
            else:
                print(f"✅ Валидный: {'Да' if result.get('valid') else 'Нет'}")
                print(f"  Регион: {result.get('location', '—')}")
                print(f"  Оператор: {result.get('carrier', '—')}")
        elif cmd == "cluster":
            if not last_results:
                print("❌ Сначала выполните поиск (search)")
                continue
            profiles = last_results.get('found', [])
            if not profiles:
                print("❌ Нет профилей для кластеризации")
                continue
            print(f"📊 Кластеризация {len(profiles)} профилей...")
            clusters = cluster_accounts(profiles)
            print(f"✅ Найдено кластеров: {len(clusters)}")
            for i, c in enumerate(clusters):
                print(f"  Кластер #{i+1}: {len(c['profiles'])} профилей, вероятность {c['confidence']}%")
        elif cmd == "report":
            if not last_results:
                print("❌ Сначала выполните поиск (search)")
                continue
            filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            html = generate_report(last_results)
            with open(filename, 'w') as f:
                f.write(html)
            print(f"📄 Отчёт сохранён: {filename}")
        else:
            print(f"❌ Неизвестная команда: {cmd}")

if __name__ == "__main__":
    main() 
