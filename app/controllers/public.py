import os
import time
from pathlib import Path
from fastapi import APIRouter, Request, Response, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from app.dependencies import get
from app.storage.telegram_provider import TelegramFileUnavailableError, TelegramSystemError

router = APIRouter(tags=["Public Files"])

# Metadata memory cache: {file_id: (record_dict, expiry_time)}
_meta_cache = {}
# Disk cache folder for hot files and video streaming
_cache_dir = Path("./data/cache")
_cache_dir.mkdir(parents=True, exist_ok=True)

def get_cached_metadata(file_id: str):
    now = time.time()
    cached = _meta_cache.get(file_id)
    if cached and cached[1] > now:
        return cached[0]
    
    r = get("files").get(file_id)
    if r:
        _meta_cache[file_id] = (r, now + 300) # Cache for 5 minutes
    return r

def serve_file_with_range(file_path: Path, mime_type: str, original_name: str, range_header: str, etag: str, is_head: bool = False):
    file_size = file_path.stat().st_size

    if not range_header or not range_header.startswith("bytes="):
        headers = {
            "ETag": etag,
            "Cache-Control": "public, max-age=31536000, immutable",
            "Access-Control-Allow-Origin": "*",
            "Accept-Ranges": "bytes",
            "Content-Length": str(file_size),
            "Content-Disposition": f'inline; filename="{original_name}"'
        }
        if is_head:
            return Response(status_code=200, media_type=mime_type, headers=headers)
        return FileResponse(str(file_path), media_type=mime_type, filename=original_name, headers=headers)

    # Parse Range: bytes=start-end
    range_str = range_header.replace("bytes=", "").strip()
    parts = range_str.split("-")
    try:
        start = int(parts[0]) if parts[0] else 0
        end = int(parts[1]) if len(parts) > 1 and parts[1] else file_size - 1
    except ValueError:
        start = 0
        end = file_size - 1

    if start >= file_size or end >= file_size or start > end:
        return Response(status_code=416, headers={"Content-Range": f"bytes */{file_size}"})

    chunk_length = (end - start) + 1

    headers = {
        "Content-Range": f"bytes {start}-{end}/{file_size}",
        "Accept-Ranges": "bytes",
        "Content-Length": str(chunk_length),
        "Content-Type": mime_type,
        "ETag": etag,
        "Cache-Control": "public, max-age=31536000, immutable",
        "Content-Disposition": f'inline; filename="{original_name}"',
        "Access-Control-Allow-Origin": "*"
    }

    if is_head:
        return Response(status_code=206, media_type=mime_type, headers=headers)

    def iter_file_chunk():
        with open(file_path, "rb") as f:
            f.seek(start)
            bytes_left = chunk_length
            while bytes_left > 0:
                read_size = min(128 * 1024, bytes_left)
                data = f.read(read_size)
                if not data:
                    break
                bytes_left -= len(data)
                yield data

    return StreamingResponse(iter_file_chunk(), status_code=206, headers=headers, media_type=mime_type)

@router.api_route("/f/{file_id}.{ext}", methods=["GET", "HEAD"])
def public_file_delivery(file_id: str, ext: str, request: Request):
    r = get_cached_metadata(file_id)
    if not r:
        raise HTTPException(404, "Berkas tidak ditemukan.")

    etag = f'"{file_id}"'
    client_etag = request.headers.get("if-none-match")
    range_header = request.headers.get("range")
    is_head = request.method == "HEAD"

    # 1. 304 Not Modified Fast-Path (0ms Latency, 0 Bandwidth)
    if client_etag and client_etag.strip() == etag:
        return Response(
            status_code=304,
            headers={
                "ETag": etag,
                "Cache-Control": "public, max-age=31536000, immutable",
                "Access-Control-Allow-Origin": "*"
            }
        )

    provider_name = r.get("storage_provider")
    storage = get("storage")
    mime_type = r.get("mime_type") or "application/octet-stream"
    original_name = r.get("original_name") or f"{file_id}.{ext}"

    # 2. Local Storage Provider Delivery (with HTTP 206 Partial Content Video Streaming)
    if provider_name == "local":
        try:
            stream = storage.open(r["storage_key"])
            local_path = Path(stream.name)
            return serve_file_with_range(local_path, mime_type, original_name, range_header, etag, is_head)
        except Exception:
            raise HTTPException(500, "Terjadi kesalahan sistem: Berkas lokal tidak dapat dibuka.")

    # 3. Telegram Storage Delivery (with Zero-Latency Local Cache & Real-Time Pass-Through Streaming)
    elif provider_name == "telegram":
        cached_file = _cache_dir / f"{file_id}.bin"

        # Ultra Fast-Path: If already in local NVMe/SSD cache, serve directly with instant HTTP 206 Range seeking
        if cached_file.exists() and cached_file.stat().st_size > 0:
            return serve_file_with_range(cached_file, mime_type, original_name, range_header, etag, is_head)

        # Cache-Miss Real-Time Pass-Through: Stream chunks directly to user while caching to disk simultaneously
        try:
            req_stream = storage.get_file_stream(r["storage_key"])
            
            def stream_and_cache_live():
                temp_cache = _cache_dir / f"{file_id}.tmp"
                try:
                    with open(temp_cache, "wb") as f_out:
                        for chunk in req_stream.iter_content(chunk_size=256 * 1024):
                            if chunk:
                                f_out.write(chunk)
                                yield chunk
                    if temp_cache.exists() and temp_cache.stat().st_size > 0:
                        temp_cache.replace(cached_file)
                except Exception:
                    # If caching fails, ensure stream still reaches the client
                    for chunk in req_stream.iter_content(chunk_size=256 * 1024):
                        if chunk:
                            yield chunk

            headers = {
                "ETag": etag,
                "Cache-Control": "public, max-age=31536000, immutable",
                "Access-Control-Allow-Origin": "*",
                "Accept-Ranges": "bytes",
                "Content-Disposition": f'inline; filename="{original_name}"'
            }
            if r.get("size"):
                headers["Content-Length"] = str(r["size"])

            if is_head:
                return Response(status_code=200, media_type=mime_type, headers=headers)

            return StreamingResponse(
                stream_and_cache_live(),
                media_type=mime_type,
                headers=headers
            )
        except TelegramFileUnavailableError:
            raise HTTPException(500, "Terjadi kesalahan sistem: Berkas sumber tidak lagi tersedia di penyimpanan Telegram.")
        except TelegramSystemError as tse:
            raise HTTPException(500, f"Terjadi kesalahan sistem: {str(tse)}")
        except Exception as e:
            raise HTTPException(500, f"Terjadi kesalahan sistem saat memuat berkas: {str(e)}")

    else:
        raise HTTPException(501, "Penyedia penyimpanan tidak didukung.")
