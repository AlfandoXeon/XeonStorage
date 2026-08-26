# 🚀 XeonStorage (v2.0)

**XeonStorage** is a modern, high-performance, centralized cloud file storage platform and developer REST API built with FastAPI, LibSQL/SQLite, and Telegram Cloud Storage.

---

## ✨ Features

- ⚡ **High-Speed Cloud Storage**: Stores files permanently on Telegram cloud with zero expiration dates.
- 🎬 **Video Streaming & Range Seeking**: Full **HTTP 206 Partial Content** support for smooth MP4/MOV video playback and instant scrubbing.
- 🧹 **Smart Automated Disk Cache Manager**: Built-in LRU eviction and TTL expiration to keep disk usage safe and lightweight for deployment on **Render, Railway, or VPS**.
- 🌐 **Full Dual-Language (Bilingual)**: English by default with instantaneous toggle to Bahasa Indonesia (`EN` / `ID`).
- 🖼️ **Dual Output Links**: Generates both raw **Direct Hotlinks** (`/f/{id}.ext`) and interactive **Web Gallery Pages** (`/v/{id}`).
- 🔐 **User Management & Security**: Modal popup authentication, user settings page for password updates, and multi-key API management.
- 📡 **Developer First REST API**: Complete RESTful API with Bearer token authentication and 40 MB max file size.
- 🎨 **Modern SaaS Design System**: Tailwind CSS dark mode, glassmorphism, responsive UI, and AOS.js scroll animations.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.12, FastAPI, Uvicorn, Starlette
- **Database**: SQLite (Development) / Turso LibSQL (Production)
- **Storage Provider**: Telegram Bot API / Local Disk Storage
- **Frontend**: HTML5, Vanilla CSS, Tailwind CSS (CDN), AOS.js, JavaScript (ES6)

---

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/AlfandoXeon/XeonStorage.git
cd XeonStorage
```

### 2. Set Up Virtual Environment
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your credentials:
```bash
cp .env.example .env
```

Example `.env`:
```env
APP_NAME=XeonStorage
APP_ENV=development
APP_HOST=127.0.0.1
APP_PORT=8000
DEFAULT_LANGUAGE=en
MAX_UPLOAD_SIZE_MB=40
CACHE_MAX_SIZE_MB=500
CACHE_TTL_HOURS=24
SESSION_SECRET=your_super_secret_session_key

# Database
DATABASE_URL=sqlite:///./data/xeonstorage.db
DATABASE_AUTH_TOKEN=

# Telegram Storage
STORAGE_PROVIDER=telegram
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHANNEL_ID=your_channel_id
TELEGRAM_API_BASE=https://api.telegram.org
```

### 5. Run the Server
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Access the application in your browser:
- **Landing Page**: `http://127.0.0.1:8000/`
- **Dashboard**: `http://127.0.0.1:8000/dashboard`
- **User Settings**: `http://127.0.0.1:8000/settings`
- **API Documentation**: `http://127.0.0.1:8000/docs-page`
- **Swagger UI**: `http://127.0.0.1:8000/docs`

---

## 📖 API Documentation

For the complete API reference, examples, and schemas in both English and Indonesian, see [API_DOCUMENTATION.md](API_DOCUMENTATION.md).

---

## 📄 License

MIT License © 2026 XeonStorage.
