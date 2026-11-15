import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { send } from "../api";
import { useAuth, useToast } from "../context";
import { useData } from "../hooks";
import type { Need } from "../types";
import { date, label } from "../utils";
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
import LoanTable from "../components/LoanTable";
export default function NeedDetail() {
  const { id } = useParams(),
    { user } = useAuth(),
    toast = useToast();
  const { data: n, loading, error, reload } = useData<Need>(`/needs/${id}`);
  const [action, setAction] = useState(""),
    [outcome, setOutcome] = useState("false"),
    [accepted, setAccepted] = useState(true),
    [intended, setIntended] = useState(true),
    [met, setMet] = useState(true),
    [conclusion, setConclusion] = useState("");
  if (loading && !n) return <Loading />;
  if (!n) return <ErrorBox message={error} />;
  const mine = n.creator_id === user?.id,
    manager = n.unit_id === user?.unit_id && user?.roles.includes("QUAN_LY"),
    completed = !!n.loans?.some((l) => l.status === "DA_HOAN_TRA");
  const canVerify = manager && !mine && completed && n.status !== "NHAP";
  const saved = () => {
    reload();
    setAction("");
    toast("Đã lưu kết quả nhu cầu.");
  };
  return (
    <>
      <Link
        className="back-link"
        to={manager && !mine ? "/effectiveness" : "/loans?tab=needs"}
      >
        <ArrowLeft size={16} /> Danh sách nhu cầu
      </Link>
      <PageHeader
        eyebrow={`NHU CẦU / NC-${String(n.id).padStart(4, "0")}`}
        title={n.purpose}
        action={
          n.purchased === null ? (
            <span className="pill">Chưa khai báo</span>
          ) : (
            <Badge status={n.status} />
          )
        }
      />
      <ErrorBox message={error} />
      <div className="detail-columns">
        <div>
          <section className="panel detail-panel">
            <h2>Phương án được ghi nhận ban đầu</h2>
            <div className="data-grid">
              <DataItem title="Người lập">{n.creator_name}</DataItem>
              <DataItem title="Đơn vị">{n.unit_name}</DataItem>
              <DataItem title="Loại tài sản">{n.category_name}</DataItem>
              <DataItem title="Nếu không mượn được">
                {label(n.alternative)}
              </DataItem>
              <DataItem title="Cần dùng từ">{date(n.start_at)}</DataItem>
              <DataItem title="Đến">{date(n.end_at)}</DataItem>
              <DataItem title="Ghi nhận lúc">{date(n.created_at)}</DataItem>
              <DataItem title="Kết quả mua mới">
                {n.purchased === null
                  ? "Chưa khai báo"
                  : n.purchased
                    ? "Đã mua mới"
                    : "Không mua mới"}
              </DataItem>
            </div>
            <div className="inline-actions">
              {mine && completed && (
                <button
                  className="btn secondary"
                  onClick={() => {
                    setOutcome(n.purchased === null ? "" : String(n.purchased));
                    setAction("outcome");
                  }}
                >
                  Khai báo kết quả mua mới
                </button>
              )}
              {canVerify &&
                (n.purchased === null ? (
                  <p className="muted">
                    Đang chờ người lập khai báo kết quả mua mới.
                  </p>
                ) : (
                  <button
                    className="btn primary"
                    onClick={() => {
                      const prior =
                        n.status === "CHO_XAC_MINH" ? null : n.verification;
                      setIntended(
                        n.alternative === "MUA_MOI" &&
                          !!prior?.intended_purchase,
                      );
                      setAccepted(n.status !== "TU_CHOI");
                      setMet(prior?.purpose_met ?? false);
                      setConclusion(prior?.conclusion || "");
                      setAction("verify");
                    }}
                  >
                    Xác minh kết quả
                  </button>
                ))}
            </div>
          </section>
          <section className="panel">
            <div className="panel-heading">
              <h2>Phiếu mượn liên kết</h2>
            </div>
            <LoanTable loans={n.loans || []} />
          </section>
        </div>
        <aside>
          <section className="panel detail-panel">
            <h2>
              {n.status === "CHO_XAC_MINH" && n.verification
                ? "Kết quả xác minh lần trước"
                : "Kết quả xác minh"}
            </h2>
            {n.verification ? (
              <>
                <DataItem title="Người xác minh">
                  {n.verification.verifier_name}
                </DataItem>
                <DataItem title="Thời điểm">
                  {date(n.verification.verified_at)}
                </DataItem>
                <DataItem title="Dự định mua mới ban đầu">
                  {n.verification.intended_purchase ? "Có" : "Không"}
                </DataItem>
                <DataItem title="Mượn đáp ứng mục đích">
                  {n.verification.purpose_met ? "Có" : "Không"}
                </DataItem>
                <p className="pre-line">{n.verification.conclusion}</p>
              </>
            ) : (
              <p className="muted">Chưa có kết quả xác minh sau hoàn trả.</p>
            )}
          </section>
        </aside>
      </div>
      {action && (
        <Modal
          title={
            action === "verify" ? "Xác minh kết quả nhu cầu" : "Kết quả mua mới"
          }
          onClose={() => setAction("")}
        >
          <ActionForm
            onCancel={() => setAction("")}
            submitLabel="Xác nhận"
            onSubmit={async () => {
              if (action === "outcome")
                await send(`/needs/${id}/outcome`, {
                  purchased: outcome === "" ? null : outcome === "true",
                });
              if (action === "verify")
                await send(`/needs/${id}/verify`, {
                  accepted,
                  intended_purchase: intended,
                  purpose_met: met,
                  conclusion,
                });
              saved();
            }}
          >
            {action === "outcome" ? (
              <Field label="Đơn vị có mua mới cho nhu cầu này không?">
                <select
                  value={outcome}
                  onChange={(e) => setOutcome(e.target.value)}
                >
                  <option value="">Chưa xác định</option>
                  <option value="false">Không mua mới</option>
                  <option value="true">Có mua mới</option>
                </select>
              </Field>
            ) : (
              <div className="form-grid">
                <label className="checkbox wide">
                  <input
                    type="checkbox"
                    checked={accepted}
                    onChange={(e) => setAccepted(e.target.checked)}
                  />
                  Chấp nhận kết quả xác minh
                </label>
                <label className="checkbox wide">
                  <input
                    type="checkbox"
                    checked={intended}
                    disabled={n.alternative !== "MUA_MOI"}
                    onChange={(e) => setIntended(e.target.checked)}
                  />
                  Xác nhận dự định mua mới ban đầu
                </label>
                <label className="checkbox wide">
                  <input
                    type="checkbox"
                    checked={met}
                    onChange={(e) => setMet(e.target.checked)}
                  />
                  Việc mượn đã đáp ứng mục đích sử dụng
                </label>
                <Field label="Kết luận đối chiếu *" wide>
                  <textarea
                    required
                    minLength={10}
                    maxLength={1000}
                    rows={4}
                    value={conclusion}
                    onChange={(e) => setConclusion(e.target.value)}
                  />
                </Field>
              </div>
            )}
          </ActionForm>
        </Modal>
      )}
    </>
  );
}
