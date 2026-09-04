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

    def list_for_user(self, user_id, limit=100, offset=0, search=None, mime_category=None):
        conditions = ["user_id=?", "deleted_at IS NULL"]
        params = [user_id]

        if search and search.strip():
            conditions.append("original_name LIKE ?")
            params.append(f"%{search.strip()}%")

        if mime_category == "image":
            conditions.append("mime_type LIKE 'image/%'")
        elif mime_category == "video":
            conditions.append("mime_type LIKE 'video/%'")
        elif mime_category == "audio":
            conditions.append("mime_type LIKE 'audio/%'")
        elif mime_category == "doc":
            conditions.append("(mime_type LIKE 'application/%' OR mime_type LIKE 'text/%')")

        where_clause = " AND ".join(conditions)
        sql = f"SELECT * FROM files WHERE {where_clause} ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        return self.db.fetchall(sql, tuple(params))

    def count_for_user(self, user_id, search=None, mime_category=None):
        conditions = ["user_id=?", "deleted_at IS NULL"]
        params = [user_id]

        if search and search.strip():
            conditions.append("original_name LIKE ?")
            params.append(f"%{search.strip()}%")

        if mime_category == "image":
            conditions.append("mime_type LIKE 'image/%'")
        elif mime_category == "video":
            conditions.append("mime_type LIKE 'video/%'")
        elif mime_category == "audio":
            conditions.append("mime_type LIKE 'audio/%'")
        elif mime_category == "doc":
            conditions.append("(mime_type LIKE 'application/%' OR mime_type LIKE 'text/%')")

        where_clause = " AND ".join(conditions)
        sql = f"SELECT COUNT(*) as count FROM files WHERE {where_clause}"
        res = self.db.fetchone(sql, tuple(params))
        return res["count"] if res else 0

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

    def global_stats(self):
        res = self.db.fetchone(
            """SELECT COUNT(*) AS total_files, COALESCE(SUM(size), 0) AS total_bytes
               FROM files WHERE deleted_at IS NULL"""
        )
        return res or {"total_files": 0, "total_bytes": 0}

