# Architecture

XeonStorage separates the web/API layer from storage.

```text
Client
  |
  +--> Web UI
  |
  +--> REST API
          |
       Controllers
          |
       Services
       /       \
Repositories  StorageProvider
    |             |
  Turso       Local/Telegram/R2/S3
```

The database contains metadata only. Large binary objects should remain in a dedicated storage backend.

The `StorageProvider` interface is intentionally small so future providers can be added without changing controllers.
