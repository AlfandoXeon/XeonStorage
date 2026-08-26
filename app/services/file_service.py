import os
import secrets
import shutil
from pathlib import Path
from datetime import datetime, timezone
from app.storage.cache_manager import CacheManager

class FileService:
    def __init__(self, repo, storage, cache_mgr: CacheManager = None):
        self.repo = repo
        self.storage = storage
        self.cache_mgr = cache_mgr or CacheManager("./data/cache", max_size_mb=500, ttl_hours=24)
        self.cache_dir = self.cache_mgr.cache_dir

    def upload(self, upload, user_id=None):
        name = Path(upload.filename or "file").name
        mime = upload.content_type or "application/octet-stream"
        ext = Path(name).suffix.lower().lstrip(".") or None
        fid = secrets.token_urlsafe(7).replace("-", "a").replace("_", "b")

        # 1. Instantly write to local high-speed disk cache FIRST
        local_cache_path = self.cache_dir / f"{fid}.bin"
        upload.file.seek(0)
        with open(local_cache_path, "wb") as f_out:
            shutil.copyfileobj(upload.file, f_out, length=256 * 1024)

        # Enforce LRU size limit to prevent Render disk overflow
        self.cache_mgr.enforce_size_limit()

        # 2. Upload to storage provider (Telegram / Local) using the local cached copy
        with open(local_cache_path, "rb") as f_in:
            result = self.storage.put(f_in, name, mime)

        record = {
            "id": fid,
            "user_id": user_id,
            "original_name": name,
            "extension": ext,
            "mime_type": mime,
            "size": result["size"] or local_cache_path.stat().st_size,
            "storage_provider": self.storage.name,
            "storage_key": result["storage_key"],
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        self.repo.create(record)
        return record

    def get(self, file_id):
        return self.repo.get(file_id)

    def list(self, user_id):
        return self.repo.list_for_user(user_id)

    def stats(self, user_id):
        return self.repo.stats(user_id)

    def delete(self, file_id, user_id):
        r = self.repo.get(file_id)
        if not r or r.get("user_id") != user_id:
            return False
        try:
            self.storage.delete(r["storage_key"])
        except Exception:
            pass
        
        # Evict local cache immediately
        cached_file = self.cache_dir / f"{file_id}.bin"
        if cached_file.exists():
            try:
                os.remove(cached_file)
            except Exception:
                pass

        self.repo.soft_delete(file_id, user_id)
        return True
