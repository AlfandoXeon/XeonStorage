import os
import time
import asyncio
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

class TelethonStreamAdapter:
    """
    Wraps any stream/file-like object ensuring .name is always a string.
    This prevents Telethon from crashing with TypeError: expected str, bytes or os.PathLike object, not int
    when SpooledTemporaryFile on Linux uses an integer descriptor as its name.
    """
    def __init__(self, stream, filename: str):
        self._stream = stream
        self.name = str(filename)

    def read(self, *args, **kwargs):
        return self._stream.read(*args, **kwargs)

    def seek(self, *args, **kwargs):
        return self._stream.seek(*args, **kwargs)

    def tell(self, *args, **kwargs):
        return self._stream.tell(*args, **kwargs)

    def __iter__(self):
        return iter(self._stream)

class TelegramFileUnavailableError(Exception):
    """Raised when a file cannot be found or is no longer available on Telegram servers."""
    pass

class TelegramSystemError(Exception):
    """Raised when Telegram API encounters connectivity or system errors."""
    pass

class TelegramStorageProvider:
    name = "telegram"

    def __init__(self, api_base: str, bot_token: str, chat_id: str, api_id: int = 0, api_hash: str = "", session_string: str = ""):
        self.api_base = (api_base or "https://api.telegram.org").rstrip("/")
        self.bot_token = bot_token
        self.chat_id = chat_id
        
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_string = session_string
        
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
        
        file_size = 0
        try:
            if hasattr(stream, "seek") and hasattr(stream, "tell"):
                stream.seek(0, os.SEEK_END)
                file_size = stream.tell()
                stream.seek(0)
            elif hasattr(stream, "fileno"):
                file_size = os.fstat(stream.fileno()).st_size
        except Exception:
            file_size = 0
            
        # Jika ukuran lebih besar dari 20MB dan kredensial MTProto tersedia, gunakan Telethon (MTProto)
        if file_size >= 20 * 1024 * 1024 and self.api_id and self.api_hash and self.session_string:
            return self._put_telethon(stream, clean_filename, mime_type, file_size)
        else:
            return self._put_bot_api(stream, clean_filename, mime_type)

    def _put_bot_api(self, stream, clean_filename: str, mime_type: str):
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

            storage_key = f"{message_id}:{file_id}" if file_id else message_id

            return {
                "storage_key": storage_key,
                "size": file_size
            }
        except requests.RequestException as e:
            raise TelegramSystemError(f"Gagal mengunggah berkas ke server Telegram via HTTP API: {str(e)}")

    def _put_telethon(self, stream, clean_filename: str, mime_type: str, file_size: int = 0):
        try:
            # We must run the Telethon upload in a new event loop because we are in a synchronous context
            # that is executed within a threadpool by FastAPI.
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                return new_loop.run_until_complete(self._async_put_telethon(stream, clean_filename, mime_type, file_size))
            finally:
                new_loop.close()
        except Exception as e:
            raise TelegramSystemError(f"Gagal mengunggah berkas ke server Telegram via MTProto: {str(e)}")

    async def _async_put_telethon(self, stream, clean_filename: str, mime_type: str, file_size: int = 0):
        from telethon import TelegramClient
        from telethon.sessions import StringSession
        from telethon.tl.types import DocumentAttributeFilename
        
        # Parse chat ID to int if it's a numeric string
        try:
            target_chat = int(self.chat_id)
        except ValueError:
            target_chat = self.chat_id
            
        client = TelegramClient(StringSession(self.session_string), self.api_id, self.api_hash)
        await client.connect()
        if not await client.is_user_authorized():
            await client.disconnect()
            raise TelegramSystemError("Session MTProto tidak valid atau telah kedaluwarsa.")
            
        # Ensure the stream is at the beginning
        stream.seek(0)
        adapter = TelethonStreamAdapter(stream, clean_filename)
        
        try:
            # Upload the file stream directly in chunks using known file_size
            uploaded_file = await client.upload_file(
                file=adapter,
                file_name=clean_filename,
                file_size=file_size if file_size > 0 else None
            )
            
            message = await client.send_file(
                target_chat,
                file=uploaded_file,
                force_document=True,
                attributes=[DocumentAttributeFilename(file_name=clean_filename)]
            )
            
            if not message or not message.document:
                raise TelegramSystemError("Gagal mendapatkan objek dokumen setelah upload MTProto.")
                
            message_id = str(message.id)
            doc_size = message.document.size
            file_id = "" 
            
            storage_key = f"{message_id}:{file_id}" if file_id else message_id
            
            return {
                "storage_key": storage_key,
                "size": doc_size
            }
        finally:
            await client.disconnect()

    def check_availability(self, key: str) -> bool:
        """Validates if the file is currently available on Telegram servers (True/False)"""
        if not self.bot_token:
            return False

        try:
            parts = key.split(":", 1)
            file_id = parts[1] if len(parts) > 1 else ""
            
            if not file_id:
                # If file_id is empty (from MTProto upload), we can't easily check via Bot API getFile.
                return True
                
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
        self._path_cache[file_id] = (file_path, now + 2700)
        return file_path

    def get_file_stream(self, key: str):
        """Streams file chunks using pooled HTTP session or MTProto"""
        if not self.bot_token:
            raise TelegramSystemError("Telegram Bot belum dikonfigurasi")

        parts = key.split(":", 1)
        message_id = parts[0]
        file_id = parts[1] if len(parts) > 1 else ""

        if file_id:
            try:
                file_path = self.resolve_file_path(file_id)
                download_url = f"{self.api_base}/file/bot{self.bot_token}/{file_path}"
                res = self.session.get(download_url, stream=True, timeout=60)
                if res.status_code in [400, 404]:
                    raise TelegramFileUnavailableError("Berkas tidak ditemukan pada server unduhan Telegram.")
                res.raise_for_status()
                return res
            except Exception as e:
                # Fall back to MTProto if Bot API fails
                if self.api_id and self.api_hash and self.session_string:
                    return self._get_stream_telethon(message_id)
                else:
                    raise TelegramSystemError(f"Gagal mengunduh streaming berkas (Bot API gagal dan MTProto tidak tersedia): {str(e)}")
        else:
            if self.api_id and self.api_hash and self.session_string:
                return self._get_stream_telethon(message_id)
            else:
                raise TelegramSystemError("MTProto credentials missing, cannot download large file.")

    def _get_stream_telethon(self, message_id: str):
        from telethon import TelegramClient
        from telethon.sessions import StringSession
        import queue
        import threading
        
        q = queue.Queue(maxsize=10)
        
        def run_downloader():
            async def download_task():
                client = TelegramClient(StringSession(self.session_string), self.api_id, self.api_hash)
                await client.connect()
                if not await client.is_user_authorized():
                    await client.disconnect()
                    q.put(Exception("Session MTProto tidak valid"))
                    return
                
                try:
                    target_chat = int(self.chat_id)
                except ValueError:
                    target_chat = self.chat_id
                    
                try:
                    message = await client.get_messages(target_chat, ids=int(message_id))
                    if not message or not message.document:
                        q.put(Exception("Pesan atau dokumen tidak ditemukan via MTProto"))
                        return
                    
                    async for chunk in client.iter_download(message.document):
                        q.put(chunk)
                    
                    q.put(None)
                except Exception as e:
                    q.put(e)
                finally:
                    await client.disconnect()

            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                new_loop.run_until_complete(download_task())
            finally:
                new_loop.close()
                
        t = threading.Thread(target=run_downloader)
        t.start()
        
        class TelethonStreamer:
            def __iter__(self):
                return self
            def __next__(self):
                item = q.get()
                if isinstance(item, Exception):
                    raise item
                if item is None:
                    raise StopIteration
                return item
                
            def iter_content(self, chunk_size=None):
                return self

        return TelethonStreamer()

    def delete(self, key: str):
        if not self.bot_token or not self.chat_id:
            return False
        parts = key.split(":", 1)
        msg_id = parts[0]
        file_id = parts[1] if len(parts) > 1 else None
        
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
