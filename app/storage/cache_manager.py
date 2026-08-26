import os
import time
import asyncio
import logging
from pathlib import Path

logger = logging.getLogger("xeonstorage.cache")

class CacheManager:
    """
    Automated Smart Disk Cache Manager with LRU Eviction & TTL Expiration
    Optimized for memory/disk constrained environments like Render, Railway, etc.
    """
    def __init__(self, cache_dir: str = "./data/cache", max_size_mb: int = 500, ttl_hours: int = 24):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.ttl_seconds = ttl_hours * 3600

    def get_total_cache_size(self) -> int:
        total = 0
        try:
            for entry in self.cache_dir.iterdir():
                if entry.is_file():
                    total += entry.stat().st_size
        except Exception:
            pass
        return total

    def touch(self, file_id: str):
        """Updates access time for LRU tracking"""
        try:
            cache_file = self.cache_dir / f"{file_id}.bin"
            if cache_file.exists():
                cache_file.touch(exist_ok=True)
        except Exception:
            pass

    def clean_expired(self) -> int:
        """Removes cache files older than TTL"""
        now = time.time()
        deleted_count = 0
        try:
            for entry in self.cache_dir.iterdir():
                if entry.is_file() and not entry.name.startswith("."):
                    mtime = entry.stat().st_mtime
                    if now - mtime > self.ttl_seconds:
                        try:
                            entry.unlink()
                            deleted_count += 1
                        except Exception:
                            pass
        except Exception as e:
            logger.warning(f"Error during expired cache cleanup: {e}")
        return deleted_count

    def enforce_size_limit(self, target_ratio: float = 0.7) -> int:
        """
        LRU (Least Recently Used) Eviction:
        If total cache size exceeds max_size_mb, removes oldest accessed files
        until cache size drops below (target_ratio * max_size).
        """
        current_size = self.get_total_cache_size()
        if current_size <= self.max_size_bytes:
            return 0

        target_size = int(self.max_size_bytes * target_ratio)
        files = []
        try:
            for entry in self.cache_dir.iterdir():
                if entry.is_file() and not entry.name.startswith("."):
                    stat = entry.stat()
                    # Use access time / modification time
                    atime = max(stat.st_atime, stat.st_mtime)
                    files.append((atime, stat.st_size, entry))
        except Exception as e:
            logger.warning(f"Error reading cache directory: {e}")
            return 0

        # Sort files by oldest access time first (LRU)
        files.sort(key=lambda x: x[0])

        freed_bytes = 0
        deleted_count = 0
        for atime, size, path in files:
            if current_size - freed_bytes <= target_size:
                break
            try:
                path.unlink(missing_ok=True)
                freed_bytes += size
                deleted_count += 1
            except Exception:
                pass

        logger.info(f"LRU Cache Pruning: freed {freed_bytes / (1024*1024):.2f} MB across {deleted_count} files.")
        return deleted_count

    def prune_all(self):
        """Runs both TTL expiration and LRU size enforcement"""
        self.clean_expired()
        self.enforce_size_limit()

    async def start_periodic_cleaner(self, interval_seconds: int = 1800):
        """Async background task that runs cache maintenance every 30 minutes"""
        while True:
            try:
                await asyncio.sleep(interval_seconds)
                self.prune_all()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"Background cache cleaner error: {e}")
                await asyncio.sleep(60)
