import sys
import asyncio
from pathlib import Path

# Ensure project root is in sys.path
root_dir = str(Path(__file__).resolve().parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.templating import Jinja2Templates

from app.config.settings import get_settings
from app.database.database import Database
from app.repositories.user_repository import UserRepository
from app.repositories.api_key_repository import ApiKeyRepository
from app.repositories.file_repository import FileRepository
from app.services.auth_service import AuthService
from app.services.file_service import FileService
from app.storage.local_provider import LocalStorageProvider
from app.storage.telegram_provider import TelegramStorageProvider
from app.storage.cache_manager import CacheManager
from app.dependencies import configure
from app.controllers.api import router as api_router
from app.controllers.web import router as web_router
from app.controllers.public import router as public_router
from app.controllers.health import router as health_router

s = get_settings()
db = Database(s)
users = UserRepository(db)
keys = ApiKeyRepository(db)
files = FileRepository(db)
storage = (TelegramStorageProvider(s.telegram_api_base, s.telegram_bot_token, s.resolved_telegram_chat_id)
         if s.storage_provider == "telegram" else LocalStorageProvider(s.local_storage_path))
cache_mgr = CacheManager(cache_dir="./data/cache", max_size_mb=s.cache_max_size_mb, ttl_hours=s.cache_ttl_hours)
file_service = FileService(files, storage, cache_mgr=cache_mgr)
auth = AuthService(users, keys, s)

configure(
    auth=auth, files=file_service, keys=keys,
    storage=storage, templates=Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    db.initialize()
    # Prune expired/excess disk cache on startup
    cache_mgr.prune_all()
    # Start periodic background cache cleaner (every 30 minutes)
    cleaner_task = asyncio.create_task(cache_mgr.start_periodic_cleaner(interval_seconds=1800))
    try:
        yield
    finally:
        cleaner_task.cancel()
        try:
            await cleaner_task
        except asyncio.CancelledError:
            pass

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI(title="XeonStorage", version="2.0.0", lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=s.session_secret, max_age=86400 * 7)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

static_path = Path(__file__).resolve().parent.parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

icon_path = Path(__file__).resolve().parent.parent / "icon"
if icon_path.exists():
    app.mount("/icon", StaticFiles(directory=str(icon_path)), name="icon")

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    fav_file = icon_path / "icon.png"
    if fav_file.exists():
        return FileResponse(str(fav_file), media_type="image/png")
    return FileResponse(status_code=404)

app.include_router(health_router)
app.include_router(api_router)
app.include_router(web_router)
app.include_router(public_router)

@app.get("/health")
def health():
    return {"success": True, "status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=s.app_host, port=s.app_port, reload=True)
