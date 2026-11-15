import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  ArrowLeft,
  CalendarDays,
  ClipboardList,
  Edit3,
  Flag,
  MapPin,
} from "lucide-react";
import { send } from "../api";
import { useAuth, useToast } from "../context";
import { useData } from "../hooks";
import type { Asset, LifecycleEvent } from "../types";
import { date, label } from "../utils";
import {
  ActionForm,
  Badge,
  DataItem,
  DeviceArt,
  Empty,
  ErrorBox,
  Field,
  Loading,
  Modal,
  PageHeader,
} from "../components/ui";
import AssetForm from "../components/AssetForm";
import LoanRequest from "../components/LoanRequest";
import DecisionActions from "../components/DecisionActions";

export default function AssetDetail() {
  const navigate = useNavigate();
  const { id } = useParams(),
    { user } = useAuth(),
    toast = useToast();
  const { data: a, loading, error, reload } = useData<Asset>(`/assets/${id}`);
  const [edit, setEdit] = useState(false),
    [request, setRequest] = useState(false),
    [action, setAction] = useState(""),
    [reason, setReason] = useState(""),
    [cancel, setCancel] = useState(false),
    [kind, setKind] = useState("DANH_GIA"),
    [decision, setDecision] = useState("TIEP_TUC"),
    [condition, setCondition] = useState("");
  const own = a?.unit_id === user?.unit_id,
    manager = !!own && !!user?.roles.includes("QUAN_LY"),
    custodian = !!own && a?.custodian_id === user?.id;
  const { data: events, reload: reloadEvents } = useData<LifecycleEvent[]>(
    a && own ? `/assets/${id}/events` : null,
  );
  if (loading && !a) return <Loading />;
  if (!a) return <ErrorBox message={error} />;
  const close = () => {
    setAction("");
    setReason("");
    setCancel(false);
    setKind("DANH_GIA");
    setCondition("");
    setDecision("TIEP_TUC");
  };
  const saved = () => {
    reload();
    reloadEvents();
    close();
    toast("Đã cập nhật tài sản.");
  };
  return (
    <>
      <Link className="back-link" to={own ? "/owned" : "/assets"}>
        <ArrowLeft size={16} /> {own ? "Tài sản đơn vị" : "Khám phá tài sản"}
      </Link>
      <PageHeader
        eyebrow={`TS-${String(a.id).padStart(4, "0")} / ${a.category_name.toUpperCase()}`}
        title={a.name}
        action={<Badge status={a.status} />}
      />
      <ErrorBox message={error} />
      <div className="asset-detail-grid">
        <section className="panel asset-summary">
          <DeviceArt
            category={a.category_name}
            name={a.name}
            image={a.image_path}
            large
          />
          <div className="asset-summary-body">
            <div className="location-line">
              <MapPin size={17} />
              {a.unit_name} — {a.location_name}
            </div>
            <h2>Thông tin hiện vật</h2>
            <p className="pre-line">
              {a.description || "Chưa có mô tả bổ sung."}
            </p>
            <div className="condition-box">
              <span>Tình trạng hiện tại</span>
              <p>{a.condition}</p>
            </div>
            <div className="data-grid">
              <DataItem title="Địa chỉ đơn vị">
                {a.unit_address || "Chưa cập nhật"}
              </DataItem>
              <DataItem title="Nơi giao nhận">{a.location_name}</DataItem>
              <DataItem title="Người phụ trách">{a.custodian_name}</DataItem>
              <DataItem title="Liên hệ">
                <a href={`mailto:${a.contact_email}`}>{a.contact_email}</a>
              </DataItem>
            </div>
            <div className="inline-actions">
              {!own && a.status === "CHO_CHIA_SE" && (
                <button
                  className="btn primary"
                  onClick={() => setRequest(true)}
                >
                  <CalendarDays size={17} /> Đặt mượn tài sản
                </button>
              )}
              {custodian && a.status !== "CHO_THU_HOI" && (
                <button className="btn secondary" onClick={() => setEdit(true)}>
                  <Edit3 size={16} /> Sửa hồ sơ
                </button>
              )}
              {custodian && a.status !== "CHO_THU_HOI" && (
                <button
                  className="btn danger"
                  onClick={() => setAction("withdraw")}
                >
                  Thu hồi tài sản
                </button>
              )}
              {manager && a.status === "CHO_DUYET" && (
                <DecisionActions
                  path={`/assets/${a.id}/review`}
                  version={a.version}
                  subject={a.name}
                  onDone={saved}
                />
              )}
              {manager &&
                !a.holding &&
                !["CHO_DUYET", "TU_CHOI", "CHO_THU_HOI"].includes(a.status) && (
                  <>
                    <button
                      className="btn secondary"
                      onClick={() => setAction("event")}
                    >
                      <Flag size={16} /> Xử lý & đánh giá vòng đời
                    </button>
                  </>
                )}
            </div>
          </div>
        </section>
        <section className="panel calendar-panel">
          <div className="panel-heading">
            <h2>
              <CalendarDays size={19} /> Lịch đã giữ
            </h2>
          </div>
          <p className="muted">
            Bao gồm thời gian sử dụng và giờ dự phòng sau trả.
          </p>
          {a.calendar?.length ? (
            a.calendar.map((r, i) => (
              <div key={i} className="calendar-slot">
                <Badge status={r.status} overdue={r.overdue} />
                <strong>{date(r.start_at)}</strong>
                <span>đến {date(r.end_at)}</span>
                {r.loan_id && (
                  <Link className="text-link" to={`/loans/${r.loan_id}`}>
                    Xem phiếu PM-{r.loan_id}
                  </Link>
                )}
              </div>
            ))
          ) : (
            <Empty text="Chưa có lịch giữ chỗ sắp tới." />
          )}
        </section>
      </div>
      {request && !own && a.status === "CHO_CHIA_SE" && (
        <LoanRequest asset={a} onClose={() => setRequest(false)} />
      )}
      {own && (
        <section className="panel history-panel">
          <div className="panel-heading">
            <h2>
              <ClipboardList size={19} /> Lịch sử vòng đời
            </h2>
          </div>
          {events?.length ? (
            <div className="timeline">
              {events.map((e) => (
                <div className="timeline-item" key={e.id}>
                  <div className="timeline-dot" />
                  <div>
                    <span className="timeline-meta">
                      {date(e.created_at)} — {e.actor_name} ({label(e.kind)})
                    </span>
                    <p>{e.content}</p>
                    {e.decision && <Badge status={e.decision} />}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <Empty text="Chưa có sự kiện vòng đời." />
          )}
        </section>
      )}
      {edit && (
        <AssetForm
          asset={a}
          onClose={() => setEdit(false)}
          onSaved={() => {
            setEdit(false);
            saved();
          }}
        />
      )}

      {action && (
        <Modal
          title={
            action === "withdraw"
              ? "Thu hồi tài sản"
              : "Xử lý & đánh giá vòng đời"
          }
          onClose={close}
        >
          <ActionForm
            submitLabel={
              action === "withdraw" ? "Thu hồi tài sản" : "Lưu thay đổi"
            }
            onCancel={close}
            onSubmit={async () => {
              if (action === "withdraw") {
                const result = await send<{
                  pending: boolean;
                  message: string;
                }>(`/assets/${id}/withdraw`, { version: a.version });
                toast(result.message);
                if (result.pending) {
                  reload();
                  reloadEvents();
                  close();
                } else navigate("/owned", { replace: true });
                return;
              }
              if (action === "event")
                await send(`/assets/${id}/events`, {
                  kind,
                  content: reason,
                  decision: kind === "DANH_GIA" ? decision : null,
                  cancel_pending: cancel,
                  condition:
                    kind === "DANH_GIA" && condition ? condition : null,
                });
              saved();
            }}
          >
            <div className="form-grid">
              {action === "withdraw" && (
                <p className="confirm-copy wide">
                  Các phiếu chờ duyệt, chờ bàn giao và biên bản chưa hoàn tất sẽ
                  được hủy và xóa.{" "}
                  {a.holding
                    ? "Tài sản đang có người mượn; sẽ tự ẩn khi hai bên hoàn tất nhận trả."
                    : "Tài sản sẽ ẩn và không còn cho mượn."}
                </p>
              )}
              {action === "event" && (
                <Field label="Loại ghi nhận" wide>
                  <select
                    value={kind}
                    onChange={(e) => setKind(e.target.value)}
                  >
                    {["DANH_GIA", "SU_CO"].map((x) => (
                      <option key={x} value={x}>
                        {x === "DANH_GIA" ? "Xử lý & đánh giá" : label(x)}
                      </option>
                    ))}
                  </select>
                </Field>
              )}
              {action !== "withdraw" && (
                <Field
                  label={action === "event" ? "Nội dung *" : "Lý do *"}
                  wide
                >
                  <textarea
                    required
                    minLength={5}
                    maxLength={action === "event" ? 1000 : 500}
                    value={reason}
                    onChange={(e) => setReason(e.target.value)}
                    rows={3}
                  />
                </Field>
              )}
              {action === "event" && kind === "DANH_GIA" && (
                <>
                  <Field label="Quyết định" wide>
                    <select
                      value={decision}
                      onChange={(e) => setDecision(e.target.value)}
                    >
                      {["TIEP_TUC", "BAO_TRI"].map((x) => (
                        <option key={x} value={x}>
                          {label(x)}
                        </option>
                      ))}
                    </select>
                  </Field>
                  <Field label="Tình trạng sau kiểm tra" wide>
                    <textarea
                      required={decision === "TIEP_TUC"}
                      minLength={2}
                      maxLength={500}
                      value={condition}
                      onChange={(e) => setCondition(e.target.value)}
                    />
                  </Field>
                </>
              )}
              {action === "event" && (
                <label className="checkbox wide">
                  <input
                    type="checkbox"
                    checked={cancel}
                    onChange={(e) => setCancel(e.target.checked)}
                  />
                  Hủy các phiếu chưa bàn giao bị ảnh hưởng
                </label>
              )}
            </div>
          </ActionForm>
        </Modal>
      )}
    </>
  );
}
