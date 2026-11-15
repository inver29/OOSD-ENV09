import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, Flag, RefreshCw } from "lucide-react";
import { send } from "../api";
import { useAuth, useToast } from "../context";
import { useData } from "../hooks";
import type { Loan } from "../types";
import { date, label, loanStageStates } from "../utils";
import {
  ActionForm,
  Badge,
  DataItem,
  ErrorBox,
  Field,
  Loading,
  Modal,
  PageHeader,
} from "../components/ui";
import DecisionActions from "../components/DecisionActions";
import HandoverPanel from "../components/HandoverPanel";
import NeedOutcome from "../components/NeedOutcome";

export default function LoanDetail() {
  const { id } = useParams(),
    { user } = useAuth(),
    toast = useToast();
  const { data: n, loading, error, reload } = useData<Loan>(`/loans/${id}`);
  const [action, setAction] = useState(""),
    [reason, setReason] = useState("");
  if (loading && !n) return <Loading />;
  if (!n) return <ErrorBox message={error} />;
  const manager =
      user?.roles.includes("QUAN_LY") && user.unit_id === n.asset_unit_id,
    borrower = user?.id === n.borrower_id;
  const close = () => {
      setAction("");
      setReason("");
    },
    saved = () => {
      close();
      reload();
      toast("Đã cập nhật phiếu mượn.");
    };
  const currentStep = loanStageStates.indexOf(n.status);
  const step =
    currentStep >= 0
      ? currentStep
      : n.handed_at
        ? 2
        : n.pickup_deadline
          ? 1
          : 0;
  return (
    <>
      <Link className="back-link" to={manager ? "/review" : "/loans"}>
        <ArrowLeft size={16} />
        Danh sách phiếu mượn
      </Link>
      <PageHeader
        eyebrow={`PHIẾU MƯỢN / PM-${String(n.id).padStart(4, "0")}`}
        title={n.asset_name}
        description={`${n.borrower_unit_name} ← ${n.asset_unit_name}`}
        action={
          <button className="btn secondary" onClick={reload}>
            <RefreshCw size={16} />
            Làm mới
          </button>
        }
      />
      <ErrorBox message={error} />
      <div className="loan-progress" aria-label="Tiến độ phiếu mượn">
        {loanStageStates.map((s, i) => (
          <div key={s} className={step >= i ? "done" : ""}>
            <span>{i + 1}</span>
            <strong>{label(s)}</strong>
          </div>
        ))}
      </div>
      <div className="detail-columns">
        <div className="detail-main">
          <section className="panel detail-panel">
            <div className="panel-heading">
              <h2>Thông tin yêu cầu</h2>
              <Badge status={n.status} overdue={n.overdue} />
            </div>
            <div className="data-grid">
              <DataItem title="Người mượn">{n.borrower_name}</DataItem>
              <DataItem title="Đơn vị mượn">{n.borrower_unit_name}</DataItem>
              <DataItem title="Nhận từ">{date(n.start_at)}</DataItem>
              <DataItem title="Trả trước">{date(n.end_at)}</DataItem>
              <DataItem title="Người xét duyệt">{n.approver_name}</DataItem>
              <DataItem title="Hạn đến nhận">
                {date(n.pickup_deadline)}
              </DataItem>
            </div>
            <div className="description-block">
              <span>Mục đích sử dụng</span>
              <p>{n.purpose}</p>
            </div>
            {n.reason && (
              <div className="condition-box">
                <span>Lý do xử lý</span>
                <p>{n.reason}</p>
              </div>
            )}
            {manager && n.status === "CHO_DUYET" && (
              <DecisionActions
                path={`/loans/${n.id}/decision`}
                subject={n.asset_name}
                onDone={saved}
              />
            )}
            <div className="inline-actions">
              {(manager || borrower) &&
                ["CHO_DUYET", "CHO_BAN_GIAO"].includes(n.status) && (
                  <button
                    className="btn secondary"
                    onClick={() => setAction("cancel")}
                  >
                    Hủy phiếu
                  </button>
                )}
              {borrower &&
                ["DANG_MUON", "CHO_XAC_NHAN_TRA"].includes(n.status) && (
                  <button
                    className="btn secondary"
                    onClick={() => setAction("incident")}
                  >
                    <Flag size={16} />
                    Báo sự cố
                  </button>
                )}
            </div>
          </section>
          <HandoverPanel loan={n} kind="GIAO" onDone={reload} />
          <HandoverPanel loan={n} kind="TRA" onDone={reload} />
          {n.need && (
            <NeedOutcome key={n.need.id} need={n.need} onDone={reload} />
          )}
        </div>
        <aside>
          <section className="panel detail-panel">
            <h2>Mốc xử lý</h2>
            <div className="milestones">
              {[
                ["Gửi yêu cầu", n.created_at],
                ["Xét duyệt", n.decided_at],
                ["Bàn giao", n.handed_at],
                ["Hoàn trả", n.returned_at],
              ].map(([t, v]) => (
                <DataItem title={t || ""} key={t}>
                  {date(v)}
                </DataItem>
              ))}
            </div>
            {!n.asset?.withdrawn && (
              <Link
                className="text-link"
                to={`${manager ? "/owned" : "/assets"}/${n.asset_id}`}
              >
                Xem hồ sơ tài sản
              </Link>
            )}
          </section>
          <section className="panel detail-panel">
            <h2>Chính sách của phiếu</h2>
            <p>{n.policy?.name}</p>
            <dl className="compact-dl">
              <div>
                <dt>Tối đa</dt>
                <dd>{n.policy?.max_days} ngày</dd>
              </div>
              <div>
                <dt>Giờ nhận</dt>
                <dd>{n.policy?.pickup_hours} giờ</dd>
              </div>
              <div>
                <dt>Dự phòng</dt>
                <dd>{n.buffer_hours ?? n.policy?.buffer_hours} giờ</dd>
              </div>
            </dl>
          </section>
        </aside>
      </div>
      {action && (
        <Modal
          title={action === "cancel" ? "Hủy phiếu mượn" : "Báo sự cố tài sản"}
          onClose={close}
        >
          <ActionForm
            onCancel={close}
            submitLabel={action === "cancel" ? "Hủy phiếu" : "Gửi sự cố"}
            onSubmit={async () => {
              if (action === "cancel")
                await send(`/loans/${id}/cancel`, { reason });
              else
                await send(`/assets/${n.asset_id}/events`, {
                  kind: "SU_CO",
                  content: reason,
                });
              saved();
            }}
          >
            <Field label={action === "cancel" ? "Lý do *" : "Mô tả sự cố *"}>
              <textarea
                required
                minLength={5}
                maxLength={500}
                rows={3}
                value={reason}
                onChange={(e) => setReason(e.target.value)}
              />
            </Field>
          </ActionForm>
        </Modal>
      )}
    </>
  );
}
