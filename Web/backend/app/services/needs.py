from sqlalchemy import exists, select

from .. import domain
from ..models import Category, Loan, Need, Verification
from .common import get_or_404, locked, upload_path


def save_need(db, actor, data):
    domain.require_member(actor)
    domain.check_period(data.start_at, data.end_at)
    category = get_or_404(db, Category, data.category_id)
    domain.require(category.active, "Loại tài sản đã ngừng hoạt động.")
    domain.require(
        data.end_at > domain.now(),
        "Không tạo nhu cầu sau khi kỳ sử dụng đã kết thúc.",
    )
    need = Need(
        unit_id=actor.unit_id,
        creator_id=actor.id,
        status="CHO_XAC_MINH",
        created_at=domain.now(),
    )
    db.add(need)
    need.category_id, need.purpose, need.start_at, need.end_at = (
        data.category_id,
        data.purpose,
        data.start_at,
        data.end_at,
    )
    need.alternative = data.alternative
    if "evidence_path" in data.model_fields_set:
        need.evidence_path = upload_path(db, actor, data.evidence_path, need.evidence_path)
    db.flush()
    db.refresh(need)
    return need


def completed_need(need_id=Need.id):
    return exists(select(Loan.id).where(Loan.need_id == need_id, Loan.status == "DA_DONG"))


def require_completed(db, need):
    domain.require(
        db.scalar(select(Loan.id).where(Loan.need_id == need.id, Loan.status == "DA_DONG").limit(1))
        is not None,
        "Nhu cầu chỉ được xử lý sau khi hoàn tất hoàn trả tài sản.",
        409,
    )


def record_outcome(db, actor, need_id, purchased):
    need = locked(db, Need, need_id)
    domain.require(need.creator_id == actor.id, "Chỉ người lập được khai báo kết quả mua mới.", 403)
    require_completed(db, need)
    if need.purchased != purchased and need.status == "DA_XAC_MINH":
        need.status = "CHO_XAC_MINH"
    need.purchased = purchased
    if need.status == "NHAP":
        need.status = "CHO_XAC_MINH"
    db.flush()
    return need


def verify(db, actor, need_id, data):
    need = locked(db, Need, need_id)
    domain.require_manager(actor, need.unit_id)
    domain.require(actor.id != need.creator_id, "Không được tự xác minh nhu cầu do mình lập.", 403)
    domain.require(
        need.status in {"CHO_XAC_MINH", "DA_XAC_MINH", "TU_CHOI"},
        "Nhu cầu chưa ở trạng thái có thể xác minh.",
        409,
    )
    require_completed(db, need)
    domain.require(
        need.purchased is not None,
        "Người lập cần khai báo kết quả mua mới trước khi xác minh.",
        409,
    )
    domain.require(
        not data.intended_purchase or need.alternative == "MUA_MOI",
        "Chỉ xác nhận dự định mua khi phương án ban đầu là Mua mới.",
    )
    verification = db.scalar(select(Verification).where(Verification.need_id == need.id))
    if not verification:
        verification = Verification(need_id=need.id)
        db.add(verification)
    verification.verifier_id, verification.verified_at = actor.id, domain.now()
    verification.intended_purchase, verification.purpose_met = (
        data.intended_purchase,
        data.purpose_met,
    )
    verification.conclusion = data.conclusion
    if "evidence_path" in data.model_fields_set:
        verification.evidence_path = upload_path(
            db, actor, data.evidence_path, verification.evidence_path
        )
    need.status = "DA_XAC_MINH" if data.accepted else "TU_CHOI"
    db.flush()
    db.refresh(need)
    return need


def indicator(db, actor, start, end, category_id=None):
    domain.require_manager(actor, actor.unit_id)
    domain.check_period(start, end)
    # SERIALIZABLE keeps need, verification and closed-loan reads consistent for this calculation.
    db.connection().exec_driver_sql("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")
    try:
        query = (
            select(Need)
            .join(Verification, Verification.need_id == Need.id)
            .where(
                Need.unit_id == actor.unit_id,
                Need.status == "DA_XAC_MINH",
                completed_need(),
                Need.purchased.is_not(None),
                Verification.intended_purchase == True,
                Need.end_at >= start,
                Need.end_at < end,
            )
        )
        if category_id:
            query = query.where(Need.category_id == category_id)
        selected = list(db.scalars(query).unique())
        rows = []
        for need in selected:
            avoided = need.verification.purpose_met and need.purchased is False
            if avoided:
                reason = "Đáp ứng nhu cầu, đã trả và không mua mới."
            elif need.purchased:
                reason = "Vẫn mua mới."
            else:
                reason = "Chưa đáp ứng mục đích."
            rows.append(
                dict(
                    id=need.id,
                    purpose=need.purpose,
                    category_name=need.category.name,
                    creator_name=need.creator.name,
                    end_at=need.end_at,
                    avoided=avoided,
                    reason=reason,
                )
            )
        denominator = len(rows)
        numerator = sum(r["avoided"] for r in rows)
        return dict(
            total=denominator,
            avoided=numerator,
            rate=round(numerator / denominator * 100, 1) if denominator else None,
            start=start,
            end=end,
            unit_name=actor.unit.name,
            rows=rows,
            assumptions=[
                "Mỗi nhu cầu tương ứng một hiện vật có thể phải mua.",
                "Chỉ đánh giá nhu cầu có lượt mượn đã hoàn trả và đã khai báo kết quả mua mới.",
                "Kỳ báo cáo tính theo giờ Việt Nam. Kết quả chỉ phản ánh các nhu cầu đủ điều kiện trong đơn vị.",
                "Phương án mua được khai báo trước kết quả mượn và được quản lý khác người lập xác minh; chỉ số dựa trên khai báo và kết quả đối chiếu.",
                "Chỉ tính tránh mua mới khi có phiếu đã đóng, đáp ứng mục đích và xác nhận không mua mới.",
                "Mỗi nhu cầu chỉ tính một lần. Kết quả phản ánh dữ liệu hiện tại, không quy đổi thành tiền.",
            ],
        )
    finally:
        # SQL Server retains the current transaction's locks until commit; reset the next transaction's level.
        db.connection().exec_driver_sql("SET TRANSACTION ISOLATION LEVEL READ COMMITTED")
