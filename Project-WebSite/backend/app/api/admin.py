from fastapi import APIRouter, Request
from sqlalchemy import select

from .. import domain
from ..db import Db
from ..models import Policy, User
from ..schemas import CatalogInput, PolicyInput, UserInput
from ..security import Actor
from ..services import admin
from ..services.common import get_or_404, user_view

router = APIRouter(tags=["Quản trị"])


def catalog_view(item):
    result = {"id": item.id, "name": item.name, "active": item.active}
    if hasattr(item, "address"):
        result["address"] = item.address
    if hasattr(item, "unit_id"):
        result.update(unit_id=item.unit_id, description=item.description)
    return result


def policy_view(item):
    return {
        "id": item.id,
        "name": item.name,
        "max_days": item.max_days,
        "buffer_hours": item.buffer_hours,
        "pickup_hours": item.pickup_hours,
        "effective_from": item.effective_from,
    }


@router.get("/lookups")
def lookups(db: Db, actor: Actor):
    result = {}
    for kind, model in admin.CATALOGS.items():
        query = select(model).order_by(model.name)
        if "QUAN_TRI" not in actor.roles:
            query = query.where(model.active == True)
        result[kind] = [catalog_view(x) for x in db.scalars(query)]
    result["people"] = [
        user_view(x)
        for x in db.scalars(
            select(User)
            .where(User.unit_id == actor.unit_id, User.active == True)
            .order_by(User.name)
        ).unique()
    ]
    policy = db.scalar(
        select(Policy)
        .where(Policy.effective_from <= domain.now())
        .order_by(Policy.effective_from.desc())
    )
    result["policy"] = policy_view(policy) if policy else None
    return result


@router.get("/admin/users")
def users(db: Db, actor: Actor):
    domain.require_admin(actor)
    return [user_view(x) for x in db.scalars(select(User).order_by(User.id)).unique()]


@router.post("/admin/users", status_code=201)
def create_user(data: UserInput, db: Db, actor: Actor):
    return user_view(admin.save_user(db, actor, data))


@router.put("/admin/users/{user_id}")
def update_user(user_id: int, data: UserInput, db: Db, actor: Actor, request: Request):
    result = admin.save_user(db, actor, data, user_id)
    request.app.state.auth.revoke_user(user_id)
    return user_view(result)


@router.post("/admin/catalog/{kind}", status_code=201)
def create_catalog(kind: str, data: CatalogInput, db: Db, actor: Actor):
    return catalog_view(admin.save_catalog(db, actor, kind, data))


@router.put("/admin/catalog/{kind}/{record_id}")
def update_catalog(kind: str, record_id: int, data: CatalogInput, db: Db, actor: Actor):
    return catalog_view(admin.save_catalog(db, actor, kind, data, record_id))


@router.delete("/admin/catalog/{kind}/{record_id}")
def delete_catalog(kind: str, record_id: int, db: Db, actor: Actor):
    domain.require_admin(actor)
    domain.require(kind in admin.CATALOGS, "Không tìm thấy danh mục.", 404)
    db.delete(get_or_404(db, admin.CATALOGS[kind], record_id))
    db.flush()
    return {"message": "Đã xóa mục chưa sử dụng."}


@router.get("/admin/policies")
def policies(db: Db, actor: Actor):
    domain.require_admin(actor)
    return [
        policy_view(x) for x in db.scalars(select(Policy).order_by(Policy.effective_from.desc()))
    ]


@router.post("/admin/policies", status_code=201)
def create_policy(data: PolicyInput, db: Db, actor: Actor):
    return policy_view(admin.save_policy(db, actor, data))


@router.put("/admin/policies/{policy_id}")
def update_policy(policy_id: int, data: PolicyInput, db: Db, actor: Actor):
    return policy_view(admin.save_policy(db, actor, data, policy_id))


@router.delete("/admin/policies/{policy_id}")
def delete_policy(policy_id: int, db: Db, actor: Actor):
    domain.require_admin(actor)
    db.delete(get_or_404(db, Policy, policy_id))
    db.flush()
    return {"message": "Đã xóa chính sách chưa sử dụng."}
