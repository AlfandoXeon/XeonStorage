# Security checklist

Before exposing XeonStorage publicly:

- Set a strong SESSION_SECRET.
- Use HTTPS.
- Never commit `.env`.
- Rotate the Telegram bot token if it was ever exposed.
- Add rate limiting.
- Add per-user/API-key upload quotas.
- Validate MIME type and file signatures.
- Consider malware scanning.
- Limit file sizes.
- Add signed/private URLs if files are not public.
- Keep Telegram Local Bot API private.
- Add audit logs and monitoring.
- Back up both metadata and objects.
