class UserRepository:
    def __init__(self, db):
        self.db = db

    def create(self, user_id, username, email, password_hash, created_at):
        self.db.execute(
            "INSERT INTO users (id,username,email,password_hash,created_at) VALUES (?,?,?,?,?)",
            (user_id, username, email, password_hash, created_at)
        )

    def by_login(self, login):
        return self.db.fetchone(
            "SELECT * FROM users WHERE username = ? OR email = ?", (login, login)
        )

    def by_id(self, user_id):
        return self.db.fetchone("SELECT * FROM users WHERE id = ?", (user_id,))

    def update_password(self, user_id, password_hash):
        self.db.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (password_hash, user_id)
        )
