import hashlib
import secrets
import uuid
from datetime import datetime, timezone

class AuthService:
    PREFIX = "XST_"

    def __init__(self, users, keys, settings):
        self.users = users
        self.keys = keys
        self.settings = settings

    @staticmethod
    def password_hash(password: str) -> str:
        return hashlib.pbkdf2_hmac(
            "sha256", password.encode(), b"xeonstorage-v1", 210000
        ).hex()

    @staticmethod
    def key_hash(key: str) -> str:
        return hashlib.sha256(key.encode()).hexdigest()

    def register(self, username: str, email: str, password: str) -> str:
        if len(password) < 8:
            raise ValueError("Password must contain at least 8 characters.")
        if self.users.by_login(username) or self.users.by_login(email):
            raise ValueError("Username or email already exists.")
        uid = str(uuid.uuid4())
        self.users.create(
            uid,
            username,
            email,
            self.password_hash(password),
            datetime.now(timezone.utc).isoformat()
        )
        return uid

    def login(self, login: str, password: str):
        user = self.users.by_login(login)
        if not user or self.password_hash(password) != user["password_hash"]:
            return None
        return user

    def change_password(self, user_id: str, current_password: str, new_password: str, confirm_password: str) -> bool:
        if new_password != confirm_password:
            raise ValueError("Konfirmasi kata sandi baru tidak cocok.")
        if len(new_password) < 8:
            raise ValueError("Kata sandi baru minimal harus 8 karakter.")

        user = self.users.by_id(user_id)
        if not user:
            raise ValueError("Pengguna tidak ditemukan.")
        if self.password_hash(current_password) != user["password_hash"]:
            raise ValueError("Kata sandi saat ini (lama) yang Anda masukkan salah.")

        new_hash = self.password_hash(new_password)
        self.users.update_password(user_id, new_hash)
        return True

    def create_api_key(self, user_id: str, name: str) -> str:
        raw = self.PREFIX + secrets.token_urlsafe(32)
        self.keys.create(
            str(uuid.uuid4()),
            user_id,
            name,
            self.key_hash(raw),
            datetime.now(timezone.utc).isoformat()
        )
        return raw

    def authenticate_api_key(self, raw: str):
        if not raw or not raw.startswith(self.PREFIX):
            return None
        return self.keys.by_hash(self.key_hash(raw))
