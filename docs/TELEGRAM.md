# Telegram storage

Telegram is treated as an object-storage backend.

The bot uploads files into a private channel/chat through the Local Bot API Server.

Recommended:

```text
XeonStorage API
      |
      | localhost/private network
      v
Telegram Local Bot API
      |
      v
Private Telegram channel
```

Do not expose the Local Bot API port to the public internet.

The current provider supports upload/delete. Public streaming should resolve Telegram file information and stream it without buffering the whole object into RAM.
