<p align="center">
  <img src="https://img.shields.io/badge/version-2.6-blue?style=for-the-badge&logo=github" alt="Version">
  <img src="https://img.shields.io/badge/python-3.8+-green?style=for-the-badge&logo=python" alt="Python">
  <img src="https://img.shields.io/badge/license-OL--CC-orange?style=for-the-badge" alt="License">
  <img src="https://img.shields.io/badge/status-stable-brightgreen?style=for-the-badge" alt="Status">
  <img src="https://img.shields.io/badge/docker-ready-2496ED?style=for-the-badge&logo=docker" alt="Docker">
  <img src="https://img.shields.io/badge/PRs-welcome-brightgreen?style=for-the-badge&logo=github" alt="PRs Welcome">
</p>

# 🔍 ClnSIt — OSINT Engine

**Server-side OSINT engine with licensing system. One file. One container. 50+ sources.**

---

## 📋 Navigation

[Features](#-features) •
[Architecture](#-architecture) •
[Quick Start](#-quick-start) •
[API](#-api) •
[Tech Stack](#-tech-stack) •
[License](#-license) •
[Contact](#-contact)

---

## 💡 Concept

> ClnSIt is a **server-side OSINT engine** that searches for profiles by username across 50+ platforms.  
> Everything runs on the server — the client just sends a username and gets back a ready-to-use JSON report with a connection graph.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔍 **50+ Sources** | GitHub, Reddit, Telegram, VK, Twitter, Instagram, TikTok, Steam, Spotify, Pinterest and more |
| 🌐 **Async Search** | Parallel requests — no waiting for each source one by one |
| 📊 **Graph Building** | Visualize all found accounts and their connections |
| ✉️ **Entity Extraction** | Extract emails, phones, links from bios |
| 🎨 **Beautiful UI** | Loading animations, progress bars, colored terminal output |
| 🔒 **Licensing System** | Protection against unauthorized use |
| 🛡️ **Code Encryption** | AES-256 core protection |
| 📁 **Auto Backup** | Database backup every 30 minutes |

---

## 🧠 Architecture

```

┌─────────────┐     /verify      ┌─────────────────┐
│   Client    │ ───────────────▶ │                 │
│  client.py  │     /search      │  Flask Server   │
│             │ ───────────────▶ │    server.py    │
└─────────────┘                  │                 │
▲                         └────────┬────────┘
│                                  │
│           ┌──────────────────────┼──────────────────────┐
│           │                      │                      │
│           ▼                      ▼                      ▼
│    ┌─────────────┐       ┌─────────────┐        ┌─────────────┐
│    │   SQLite    │       │   OSINT     │        │    Logs     │
│    │  Database   │       │    Core     │        │  server.log │
│    └─────────────┘       └─────────────┘        └─────────────┘
│                                  │
│           ┌──────────────────────┼──────────────────────┐
│           │                      │                      │
│           ▼                      ▼                      ▼
│    ┌─────────────┐       ┌─────────────┐        ┌─────────────┐
│    │    httpx    │       │  curl_cffi  │        │  Playwright │
│    │  (HTTP/2)   │       │  (Cloudflare)│        │  (JS sites) │
│    └─────────────┘       └─────────────┘        └─────────────┘
│
▼
┌─────────────────────────────────────────────────────────────────────┐
│                        JSON Response with Graph                     │
└─────────────────────────────────────────────────────────────────────┘

```

**How it works:** The client sends a request with a license key and username. The server validates the key, executes the OSINT search through the core engine, and returns a structured JSON report with a complete connection graph. The client never sees the search logic — everything runs on the server.

---

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```bash
# Clone repository
git clone https://github.com/PurgeLabs/clnsit.git
cd clnsit

# Build image
docker build -t clnsit-server .

# Run container
docker run -d \
    --name clnsit \
    -p 5000:5000 \
    -v $(pwd)/data:/app/data \
    -v $(pwd)/logs:/app/logs \
    clnsit-server

# View logs
docker logs -f clnsit
```

Option 2: Local Setup

```bash
# Clone repository
git clone https://github.com/PurgeLabs/clnsit.git
cd clnsit

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Run server
python server.py
```

Option 3: Client Only (for users)

```bash
# Install dependencies
pip install requests

# Download client
wget https://raw.githubusercontent.com/PurgeLabs/clnsit/main/client.py

# Run
python client.py
```

<details>
<summary>⚙️ Advanced: Environment Variables</summary>

Variable Description Default
SECRET_KEY Master key for license generation Generated on first run
FLASK_ENV Flask environment mode production
PORT Server port 5000

</details>

---

🏗️ Tech Stack

Component Technology Purpose
Server Flask + SQLite Request handling, license storage
OSINT Core httpx + curl_cffi + selectolax + Playwright Profile search and parsing
Client Python + requests User interface
Encryption Fernet (AES-256) Code protection
Container Docker Universal deployment
Cloud Render / VPS Hosting

<details>
<summary>📁 Project Structure</summary>

```
clnsit/
├── server.py              # Flask server + OSINT core (main file)
├── client.py              # Client for users
├── genkey.py              # License key generator
├── requirements.txt       # Dependencies
├── Dockerfile             # Containerization
├── README.md              # Documentation
├── LICENSE                # OL-CC license
├── data/
│   ├── database.db        # License database
│   ├── backup.db          # Backup copy
│   └── secret.json        # Master key
└── logs/
    └── server.log         # Server logs
```

</details>

---

📡 API

Endpoint Method Description
/ GET Server status
/verify POST Check license key
/search POST OSINT search by username
/admin/generate POST Generate new key
/admin/revoke POST Revoke key
/admin/stats GET Statistics

Example Request: /search

```json
{
  "key": "CLN-XXXX-XXXX-XXXX",
  "username": "example"
}
```

Example Response

```json
{
  "success": true,
  "username": "example",
  "found": 4,
  "total": 50,
  "graph": {
    "axiom": "example",
    "nodes": {
      "github_example": {
        "type": "profile",
        "source": "github",
        "url": "https://github.com/example",
        "weight": 0.8,
        "bio": "Developer, security researcher"
      }
    },
    "edges": [
      ["example", "github_example", 0.8]
    ]
  }
}
```

---

🗃️ Database Schema

```sql
licenses (
    key TEXT PRIMARY KEY,
    is_active INTEGER DEFAULT 1,
    expires_at INTEGER,
    user_id TEXT,
    created_at INTEGER
);
```

---

🔧 Dependencies

```txt
flask==3.0.3
flask-cors==4.0.1
cryptography==42.0.8
httpx[http2]>=0.28.0
curl_cffi>=0.7.0
selectolax>=0.3.0
playwright>=1.40.0
```

---

🔐 Security

· Master key stored in data/secret.json
· Core encrypted with AES-256
· All endpoints validate input
· Full action logging

---

🔑 Licensing

Generate keys with genkey.py:

```bash
python genkey.py
```

Keys are validated via /verify and grant access to /search.



📜 License

OL-CC (Open Learn — Close Code)

✅ Allowed       ❌ Prohibited
Study the code | Commercial use without permission
Educational use | Redistribution as your own
Personal modifications | Illegal use
Learning forks |  Removing attribution

Full text: LICENSE

---

🤝 Contributing

1. Fork the repository
2. Create a feature branch (git checkout -b feature/amazing)
3. Commit your changes (git commit -m 'Add amazing feature')
4. Push to the branch (git push origin feature/amazing)
5. Open a Pull Request

---

📬 Contact


Telegram @PurgeLabs
Email supportp49dev@gmail.com
GitHub PurgeLabs
Donation DonationAlerts

---

<p align="center">
  <sub>Built with ❤️ by Purge Labs</sub>
</p>

<p align="center">
  <sub>© 2026 Purge Labs. All rights reserved.</sub>
</p>
``` 
