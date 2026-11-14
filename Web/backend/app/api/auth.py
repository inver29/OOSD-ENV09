from fastapi import APIRouter, Request, Response
from sqlalchemy import select

from .. import domain
from ..db import Db
from ..models import User
from ..schemas import LoginInput, PasswordInput
from ..security import COOKIE, Actor, hash_password, verify_password
from ..services.common import user_view

router = APIRouter(prefix="/auth", tags=["Tài khoản"])


@router.post("/login")
def login(data: LoginInput, request: Request, response: Response, db: Db):
    store = request.app.state.auth
    store.check_attempt(
        f"{request.client.host if request.client else 'local'}:{data.username.lower()}"
    )
    user = db.scalar(select(User).where(User.username == data.username.lower()))
    domain.require(
        user is not None
        and user.active
        and user.unit.active
        and verify_password(data.password, user.password_hash),
        "Tên đăng nhập hoặc mật khẩu không đúng, hoặc tài khoản đã bị khóa.",
        401,
    )
    previous = request.cookies.get(COOKIE)
    if previous:
        store.revoke(previous)
    token, session = store.create(user.id)
    response.set_cookie(
        COOKIE,
        token,
        httponly=True,
        secure=request.app.state.config.cookie_secure,
        samesite="lax",
        max_age=request.app.state.config.session_hours * 3600,
        path="/",
    )
    return {"user": user_view(user), "csrf_token": session.csrf}


@router.get("/me")
def me(actor: Actor, request: Request):
    return {"user": user_view(actor), "csrf_token": request.state.login_session.csrf}


@router.post("/logout")
def logout(actor: Actor, request: Request, response: Response):
    request.app.state.auth.revoke(request.cookies.get(COOKIE, ""))
    response.delete_cookie(COOKIE, path="/")
    return {"message": "Đã đăng xuất."}


@router.post("/password")
def password(data: PasswordInput, actor: Actor, db: Db, request: Request, response: Response):
    domain.require(
        verify_password(data.current_password, actor.password_hash),
        "Mật khẩu hiện tại chưa đúng.",
    )
    actor.password_hash = hash_password(data.new_password)
    db.flush()
    request.app.state.auth.revoke_user(actor.id)
    response.delete_cookie(COOKIE, path="/")
    return {"message": "Đã đổi mật khẩu. Vui lòng đăng nhập lại."}
