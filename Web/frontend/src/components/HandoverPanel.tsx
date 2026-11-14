import { useState } from "react";
import { send } from "../api";
import { useAuth, useToast } from "../context";
import type { Loan, Report } from "../types";
import { date, errorText } from "../utils";
import {
  ActionForm,
  Attachment,
  Badge,
  ErrorBox,
  Field,
  FileLink,
  Modal,
} from "./ui";

function ReportForm({
  loan,
  record,
  kind,
  returning,
  onClose,
  onDone,
}: {
  loan: Loan;
  record?: Report;
  kind: "GIAO" | "TRA";
  returning: boolean;
  onClose: () => void;
  onDone: () => void;
}) {
  const [content, setContent] = useState(
      record?.content || (kind === "GIAO" ? loan.asset?.condition || "" : ""),
    ),
    [condition, setCondition] = useState(record?.condition || "Đạt"),
    [file, setFile] = useState(record?.evidence_path || null),
    [uploading, setUploading] = useState(false),
    [receiver, setReceiver] = useState(() => {
      const preferred =
        record?.receiver_id ||
        loan.reports?.find((r) => r.kind === "GIAO")?.giver_id;
      return (
        loan.return_managers?.find((u) => u.id === preferred)?.id ||
        loan.return_managers?.[0]?.id ||
        0
      );
    });
  return (
    <Modal
      title={
        returning
          ? "Trả tài sản"
          : kind === "GIAO"
            ? "Bàn giao tài sản"
            : "Kiểm tra nhận trả"
      }
      onClose={onClose}
    >
      <ActionForm
        disabled={uploading}
        onCancel={onClose}
        submitLabel={
          returning
            ? "Xác nhận trả tài sản"
            : kind === "GIAO"
              ? "Xác nhận bàn giao"
              : "Lưu & xác nhận nhận trả"
        }
        onSubmit={async () => {
          const data = {
            content,
            condition,
            evidence_path: file,
            version: record?.version || null,
          };
          if (returning)
            await send(`/loans/${loan.id}/return`, {
              ...data,
              receiver_id: receiver || null,
            });
          else
            await send(`/loans/${loan.id}/reports`, {
              ...data,
              kind,
              confirm_self: true,
            });
          onDone();
          onClose();
        }}
      >
        <div className="form-grid">
          <Field label="Tình trạng hiện vật *" wide>
            <select
              value={condition}
              onChange={(e) => setCondition(e.target.value)}
            >
              <option>Đạt</option>
              {kind === "TRA" && <option>Hư hỏng</option>}
            </select>
          </Field>
          <Field label="Nội dung kiểm tra / Phụ kiện *" wide>
            <textarea
              required
              minLength={5}
              maxLength={1000}
              rows={3}
              value={content}
              onChange={(e) => setContent(e.target.value)}
            />
          </Field>
          {returning && (loan.return_managers?.length || 0) > 1 && (
            <Field label="Quản lý nhận trả" wide>
              <select
                value={receiver}
                onChange={(e) => setReceiver(+e.target.value)}
              >
                {loan.return_managers?.map((u) => (
                  <option value={u.id} key={u.id}>
                    {u.name}
                  </option>
                ))}
              </select>
            </Field>
          )}
          <Field label="Ảnh hiện trạng / Chứng từ" wide>
            <Attachment
              value={file}
              onChange={setFile}
              onBusyChange={setUploading}
            />
          </Field>
        </div>
        <p className="form-caption">
          Bấm xác nhận nghĩa là bạn đồng ý với nội dung và tình trạng trên.{" "}
          {record
            ? "Thay đổi nội dung sẽ yêu cầu bên còn lại xác nhận lại."
            : ""}
        </p>
      </ActionForm>
    </Modal>
  );
}

export default function HandoverPanel({
  loan,
  kind,
  onDone,
}: {
  loan: Loan;
  kind: "GIAO" | "TRA";
  onDone: () => void;
}) {
  const { user } = useAuth(),
    toast = useToast();
  const [edit, setEdit] = useState(false),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [cancel, setCancel] = useState(false);
  const record = loan.reports?.find((r) => r.kind === kind),
    manager =
      user?.roles.includes("QUAN_LY") && user.unit_id === loan.asset_unit_id,
    borrower = user?.id === loan.borrower_id;
  const active =
    kind === "GIAO"
      ? loan.status === "DA_DUYET"
      : ["DANG_MUON", "CHO_XAC_NHAN_TRA"].includes(loan.status);
  const canPrepare =
    active &&
    (kind === "GIAO"
      ? manager
      : borrower || (manager && loan.status === "CHO_XAC_NHAN_TRA"));
  if (!record && !canPrepare) return null;
  const party =
      record &&
      (record.giver_id === user?.id || record.receiver_id === user?.id),
    signed =
      record &&
      (record.giver_id === user?.id
        ? record.giver_confirmed_at
        : record.receiver_confirmed_at),
    done = () => {
      onDone();
      toast("Đã cập nhật giao nhận.");
    };
  async function confirm() {
    if (!record) return;
    setBusy(true);
    setError("");
    try {
      await send(`/loans/${loan.id}/reports/${record.id}/confirm`, {
        version: record.version,
      });
      done();
    } catch (e) {
      setError(errorText(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="panel detail-panel">
      <div className="panel-heading">
        <h2>{kind === "GIAO" ? "Bàn giao tài sản" : "Hoàn trả tài sản"}</h2>
        {record && <Badge status={record.status} entity="handover" />}
      </div>
      <ErrorBox message={error} />
      {record && (
        <>
          <div className="record-meta">
            <span>
              Biên bản #{record.id} (Phiên bản {record.version})
            </span>
            <strong>{record.condition}</strong>
          </div>
          <p className="record-content pre-line">{record.content}</p>
          {record.evidence_path && (
            <FileLink file={record.evidence_path}>Xem ảnh / Chứng từ</FileLink>
          )}
          <div className="signature-grid">
            {[
              ["BÊN GIAO", record.giver_name, record.giver_confirmed_at],
              ["BÊN NHẬN", record.receiver_name, record.receiver_confirmed_at],
            ].map(([role, name, at]) => (
              <div key={role} className={at ? "signed" : ""}>
                <span>{role}</span>
                <strong>{name}</strong>
                <small>
                  {at ? `Đã xác nhận lúc ${date(at)}` : "Chưa xác nhận"}
                </small>
              </div>
            ))}
          </div>
        </>
      )}
      <div className="inline-actions">
        {record &&
          party &&
          !signed &&
          !["HOAN_TAT", "DA_HUY"].includes(record.status) &&
          active && (
            <button className="btn primary" disabled={busy} onClick={confirm}>
              {busy
                ? "Đang xác nhận…"
                : kind === "GIAO"
                  ? borrower
                    ? "Đã nhận tài sản"
                    : "Xác nhận bàn giao"
                  : manager
                    ? "Xác nhận đã nhận trả"
                    : "Xác nhận trả tài sản"}
            </button>
          )}
        {canPrepare && record?.status !== "HOAN_TAT" && (
          <button
            className={`btn ${!record ? "primary" : "secondary"}`}
            onClick={() => setEdit(true)}
          >
            {!record
              ? kind === "GIAO"
                ? "Bàn giao tài sản"
                : borrower
                  ? "Trả tài sản"
                  : "Kiểm tra nhận trả"
              : record.status === "DA_HUY"
                ? "Mở lại biên bản"
                : "Chỉnh sửa biên bản"}
          </button>
        )}
        {manager &&
          active &&
          record &&
          !["HOAN_TAT", "DA_HUY"].includes(record.status) && (
            <button className="btn subtle" onClick={() => setCancel(true)}>
              Hủy biên bản
            </button>
          )}
      </div>
      {edit && (
        <ReportForm
          loan={loan}
          record={record}
          kind={kind}
          returning={kind === "TRA" && !!borrower}
          onClose={() => setEdit(false)}
          onDone={done}
        />
      )}
      {cancel && record && (
        <Modal title="Hủy biên bản" onClose={() => setCancel(false)}>
          <ActionForm
            submitLabel="Hủy biên bản"
            onCancel={() => setCancel(false)}
            onSubmit={async () => {
              await send(`/loans/${loan.id}/reports/${record.id}/cancel`, {
                version: record.version,
              });
              setCancel(false);
              done();
            }}
          >
            <p className="confirm-copy">
              Hủy biên bản và các xác nhận đang có?
            </p>
          </ActionForm>
        </Modal>
      )}
    </section>
  );
}
