class ApiKeyRepository:
    def __init__(self, db): self.db = db
    def create(self, key_id, user_id, name, key_hash, created_at):
        self.db.execute(
            "INSERT INTO api_keys (id,user_id,name,key_hash,active,created_at) VALUES (?,?,?,?,1,?)",
            (key_id,user_id,name,key_hash,created_at))
    def by_hash(self, key_hash):
        return self.db.fetchone(
            "SELECT * FROM api_keys WHERE key_hash = ? AND active = 1", (key_hash,))
    def list_for_user(self, user_id):
        return self.db.fetchall(
            "SELECT id,name,active,created_at FROM api_keys WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,))
    def revoke(self, key_id, user_id):
        self.db.execute(
            "UPDATE api_keys SET active=0 WHERE id=? AND user_id=?", (key_id,user_id))
