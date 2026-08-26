class FileRepository:
    def __init__(self, db):
        self.db = db

    def create(self, record):
        self.db.execute("""INSERT INTO files
        (id, user_id, original_name, extension, mime_type, size, storage_provider, storage_key, created_at, deleted_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
            record["id"],
            record["user_id"],
            record["original_name"],
            record["extension"],
            record["mime_type"],
            record["size"],
            record["storage_provider"],
            record["storage_key"],
            record["created_at"],
            None
        ))

    def get(self, file_id):
        return self.db.fetchone(
            "SELECT * FROM files WHERE id=? AND deleted_at IS NULL",
            (file_id,)
        )

    def list_for_user(self, user_id, limit=100):
        return self.db.fetchall(
            "SELECT * FROM files WHERE user_id=? AND deleted_at IS NULL ORDER BY created_at DESC LIMIT ?",
            (user_id, limit)
        )

    def stats(self, user_id):
        res = self.db.fetchone(
            """SELECT COUNT(*) AS files, COALESCE(SUM(size), 0) AS bytes
               FROM files WHERE user_id=? AND deleted_at IS NULL""",
            (user_id,)
        )
        return res or {"files": 0, "bytes": 0}

    def soft_delete(self, file_id, user_id):
        self.db.execute(
            "UPDATE files SET deleted_at=CURRENT_TIMESTAMP WHERE id=? AND user_id=?",
            (file_id, user_id)
        )
