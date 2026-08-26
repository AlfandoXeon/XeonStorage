import os
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

class TelegramFileUnavailableError(Exception):
    """Raised when a file cannot be found or is no longer available on Telegram servers."""
    pass

class TelegramSystemError(Exception):
    """Raised when Telegram API encounters connectivity or system errors."""
    pass

class TelegramStorageProvider:
    name = "telegram"

    def __init__(self, api_base: str, bot_token: str, chat_id: str):
        self.api_base = (api_base or "https://api.telegram.org").rstrip("/")
        self.bot_token = bot_token
        self.chat_id = chat_id
        
        # In-memory path cache: {file_id: (file_path, expiry_timestamp)}
        self._path_cache = {}
        
        # High-performance persistent HTTP session with connection pooling
        self.session = requests.Session()
        retries = Retry(total=2, backoff_factor=0.3, status_forcelist=[500, 502, 503, 504])
        adapter = HTTPAdapter(pool_connections=100, pool_maxsize=200, max_retries=retries)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    @property
    def base(self):
        return f"{self.api_base}/bot{self.bot_token}"

    def put(self, stream, filename: str, mime_type: str):
        if not self.bot_token or not self.chat_id:
            raise TelegramSystemError("Telegram Bot Token atau Chat ID belum dikonfigurasi di .env")

        clean_filename = os.path.basename(filename or "file")
        try:
            r = self.session.post(
                f"{self.base}/sendDocument",
                data={"chat_id": self.chat_id},
                files={"document": (clean_filename, stream, mime_type or "application/octet-stream")},
                timeout=120
            )
            r.raise_for_status()
            j = r.json()
            if not j.get("ok"):
                raise TelegramSystemError(f"Telegram upload error: {j}")

            doc = j["result"].get("document", {})
            message_id = str(j["result"]["message_id"])
            file_id = doc.get("file_id", "")
            file_size = int(doc.get("file_size", 0))

            # Store compound key: message_id:file_id
            storage_key = f"{message_id}:{file_id}" if file_id else message_id

            return {
                "storage_key": storage_key,
                "size": file_size
            }
        except requests.RequestException as e:
            raise TelegramSystemError(f"Gagal mengunggah berkas ke server Telegram: {str(e)}")

    def check_availability(self, key: str) -> bool:
        """Validates if the file is currently available on Telegram servers (True/False)"""
        if not self.bot_token:
            return False

        try:
            parts = key.split(":", 1)
            file_id = parts[1] if len(parts) > 1 else parts[0]
            
            # Check cached path first
            now = time.time()
            cached = self._path_cache.get(file_id)
            if cached and cached[1] > now:
                return True

            r = self.session.get(f"{self.base}/getFile", params={"file_id": file_id}, timeout=15)
            if r.status_code != 200:
                return False
            j = r.json()
            return bool(j.get("ok") and j.get("result", {}).get("file_path"))
        except Exception:
            return False

    def resolve_file_path(self, file_id: str) -> str:
        """Resolves file_path with in-memory caching and availability validation"""
        now = time.time()
        cached = self._path_cache.get(file_id)
        if cached and cached[1] > now:
            return cached[0]

        try:
            r = self.session.get(f"{self.base}/getFile", params={"file_id": file_id}, timeout=20)
        except requests.RequestException as e:
            raise TelegramSystemError(f"Gagal menghubungi server Telegram: {str(e)}")

        if r.status_code in [400, 404]:
            raise TelegramFileUnavailableError("Berkas tidak lagi tersedia di penyimpanan Telegram (berkas mungkin telah dihapus).")

        try:
            j = r.json()
        except Exception:
            raise TelegramSystemError("Respon tidak valid dari server Telegram.")

        if not j.get("ok"):
            err_desc = j.get("description", "File not found")
            raise TelegramFileUnavailableError(f"Berkas tidak tersedia di Telegram: {err_desc}")

        file_path = j["result"]["file_path"]
        # Cache path for 45 minutes
        self._path_cache[file_id] = (file_path, now + 2700)
        return file_path

    def get_file_stream(self, key: str):
        """Streams file chunks using pooled HTTP session with availability checks"""
        if not self.bot_token:
            raise TelegramSystemError("Telegram Bot belum dikonfigurasi")

        parts = key.split(":", 1)
        file_id = parts[1] if len(parts) > 1 else parts[0]

        file_path = self.resolve_file_path(file_id)
        download_url = f"{self.api_base}/file/bot{self.bot_token}/{file_path}"

        try:
            res = self.session.get(download_url, stream=True, timeout=60)
            if res.status_code in [400, 404]:
                raise TelegramFileUnavailableError("Berkas tidak ditemukan pada server unduhan Telegram.")
            res.raise_for_status()
            return res
        except requests.RequestException as e:
            raise TelegramSystemError(f"Gagal mengunduh streaming berkas dari Telegram: {str(e)}")

    def delete(self, key: str):
        if not self.bot_token or not self.chat_id:
            return False
        parts = key.split(":", 1)
        msg_id = parts[0]
        file_id = parts[1] if len(parts) > 1 else None
        
        # Evict from path cache
        if file_id and file_id in self._path_cache:
            del self._path_cache[file_id]

        try:
            r = self.session.post(
                f"{self.base}/deleteMessage",
                data={"chat_id": self.chat_id, "message_id": msg_id},
                timeout=20
            )
            return r.status_code == 200
        except Exception:
            return False
