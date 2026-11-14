import hashlib
import secrets
import threading
from collections import defaultdict
from dataclasses import dataclass
from datetime import timedelta
from time import monotonic
from typing import Annotated

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from fastapi import Depends, Request
from sqlalchemy import select

from . import domain
from .db import Db
from .models import User

password_hasher = PasswordHasher()
COOKIE = "env09_session"


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, encoded: str) -> bool:
    try:
        return password_hasher.verify(encoded, password)
    except (VerificationError, InvalidHashError):
        return False


@dataclass(frozen=True)
class LoginSession:
    user_id: int
    csrf: str
    expires_at: object


class SessionStore:
    """One-process server sessions: logout and account changes revoke access immediately."""

    def __init__(self, hours: int):
        self.hours = hours
        self._sessions: dict[str, LoginSession] = {}
        self._attempts: dict[str, list[float]] = defaultdict(list)
        self._lock = threading.Lock()

    @staticmethod
    def key(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    def create(self, user_id: int) -> tuple[str, LoginSession]:
        token = secrets.token_urlsafe(48)
        entry = LoginSession(
            user_id,
            secrets.token_urlsafe(32),
            domain.now() + timedelta(hours=self.hours),
        )
        with self._lock:
            self._sessions = {
                k: v for k, v in self._sessions.items() if v.expires_at > domain.now()
            }
            self._sessions[self.key(token)] = entry
        return token, entry

    def get(self, token: str) -> LoginSession | None:
        with self._lock:
            value = self._sessions.get(self.key(token))
            return value if value and value.expires_at > domain.now() else None

    def revoke(self, token: str):
        with self._lock:
            self._sessions.pop(self.key(token), None)

    def revoke_user(self, user_id: int):
        with self._lock:
            self._sessions = {k: v for k, v in self._sessions.items() if v.user_id != user_id}

    def check_attempt(self, key: str):
        with self._lock:
            stamp = monotonic()
            self._attempts = defaultdict(
                list,
                {
                    k: [t for t in v if stamp - t < 300]
                    for k, v in self._attempts.items()
                    if v and stamp - v[-1] < 300
                },
            )
            domain.require(
                len(self._attempts[key]) < 10,
                "Bạn thử đăng nhập quá nhiều lần. Hãy thử lại sau 5 phút.",
                429,
            )
            self._attempts[key].append(stamp)


def current_user(request: Request, db: Db) -> User:
    token = request.cookies.get(COOKIE, "")
    entry = request.app.state.auth.get(token)
    domain.require(entry is not None, "Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.", 401)
    user = db.scalar(select(User).where(User.id == entry.user_id))
    domain.require(
        user is not None and user.active and user.unit.active,
        "Tài khoản hoặc đơn vị đã ngừng hoạt động.",
        401,
    )
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        domain.require(
            secrets.compare_digest(request.headers.get("X-CSRF-Token", ""), entry.csrf),
            "Phiên thao tác không hợp lệ. Vui lòng tải lại trang.",
            403,
        )
    request.state.login_session = entry
    return user


Actor = Annotated[User, Depends(current_user)]
