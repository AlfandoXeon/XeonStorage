from pathlib import Path
import base64
import requests
from app.config.settings import Settings

class TursoClient:
    def __init__(self, url: str, auth_token: str):
        cleaned_url = url.replace("libsql://", "https://").rstrip("/")
        if not cleaned_url.startswith("https://") and not cleaned_url.startswith("http://"):
            cleaned_url = f"https://{cleaned_url}"
        self.url = f"{cleaned_url}/v2/pipeline"
        self.headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }

    def execute(self, sql: str, args=()):
        pos_args = []
        for a in args:
            if a is None:
                pos_args.append({"type": "null"})
            elif isinstance(a, bool):
                pos_args.append({"type": "integer", "value": "1" if a else "0"})
            elif isinstance(a, int):
                pos_args.append({"type": "integer", "value": str(a)})
            elif isinstance(a, float):
                pos_args.append({"type": "float", "value": a})
            elif isinstance(a, bytes):
                pos_args.append({"type": "blob", "base64": base64.b64encode(a).decode()})
            else:
                pos_args.append({"type": "text", "value": str(a)})

        stmt = {"sql": sql}
        if pos_args:
            stmt["args"] = pos_args

        payload = {"requests": [{"type": "execute", "stmt": stmt}, {"type": "close"}]}
        r = requests.post(self.url, headers=self.headers, json=payload, timeout=20)
        r.raise_for_status()
        data = r.json()
        res = data["results"][0]
        if res.get("type") == "error":
            raise RuntimeError(res.get("error", {}).get("message", "Turso error"))

        exec_res = res.get("response", {}).get("result", {})
        cols = [c["name"] for c in exec_res.get("cols", [])]
        rows = []
        for row in exec_res.get("rows", []):
            parsed_row = []
            for col in row:
                t = col.get("type")
                v = col.get("value")
                if t == "null":
                    parsed_row.append(None)
                elif t == "integer":
                    parsed_row.append(int(v))
                elif t == "float":
                    parsed_row.append(float(v))
                else:
                    parsed_row.append(v)
            rows.append(parsed_row)
        return cols, rows

class Database:
    def __init__(self, settings: Settings):
        self.turso = None
        self.sqlite = None

        if settings.database_url.startswith("libsql://") or settings.database_url.startswith("https://"):
            self.turso = TursoClient(settings.database_url, settings.database_auth_token)
        else:
            import sqlite3
            path = settings.database_url.replace("sqlite:///", "", 1)
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            self.sqlite = sqlite3.connect(path, check_same_thread=False)
            self.sqlite.row_factory = sqlite3.Row

    def execute(self, sql, args=()):
        if self.turso:
            return self.turso.execute(sql, args)
        cur = self.sqlite.cursor()
        cur.execute(sql, args)
        self.sqlite.commit()
        return cur

    def fetchone(self, sql, args=()):
        if self.turso:
            cols, rows = self.turso.execute(sql, args)
            if not rows:
                return None
            return dict(zip(cols, rows[0]))
        cur = self.sqlite.cursor()
        cur.execute(sql, args)
        row = cur.fetchone()
        return dict(row) if row else None

    def fetchall(self, sql, args=()):
        if self.turso:
            cols, rows = self.turso.execute(sql, args)
            return [dict(zip(cols, row)) for row in rows]
        cur = self.sqlite.cursor()
        cur.execute(sql, args)
        return [dict(row) for row in cur.fetchall()]

    def initialize(self):
        tables = [
            """CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )""",
            """CREATE TABLE IF NOT EXISTS api_keys (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                key_hash TEXT NOT NULL UNIQUE,
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            )""",
            """CREATE TABLE IF NOT EXISTS files (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                original_name TEXT NOT NULL,
                extension TEXT,
                mime_type TEXT,
                size INTEGER NOT NULL,
                storage_provider TEXT NOT NULL,
                storage_key TEXT NOT NULL,
                created_at TEXT NOT NULL,
                deleted_at TEXT
            )""",
            "CREATE INDEX IF NOT EXISTS idx_files_user ON files(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_files_created ON files(created_at)"
        ]
        for sql in tables:
            self.execute(sql)
