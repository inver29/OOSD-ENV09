import { useState } from "react";
import { send } from "../api";
import { errorText } from "../utils";
import { ActionForm, ErrorBox, Field, Modal } from "./ui";

export default function DecisionActions({
  path,
  version,
  subject,
  embedded = false,
  onCancel,
  onDone,
}: {
  path: string;
  version?: string;
  subject?: string;
  embedded?: boolean;
  onCancel?: () => void;
  onDone: () => void;
}) {
  const [action, setAction] = useState<"approve" | "reject" | null>(null),
    [reason, setReason] = useState(""),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const close = () => {
    setAction(null);
    setReason("");
    setError("");
  };
  async function decide(approve: boolean) {
    await send(path, {
      approve,
      reason: approve ? "" : reason,
      ...(version ? { version } : {}),
    });
    close();
    onDone();
  }
  async function approveInDialog() {
    setBusy(true);
    setError("");
    try {
      await decide(true);
    } catch (e) {
      setError(errorText(e));
    } finally {
      setBusy(false);
    }
  }
  const form = action && (
    <ActionForm
      submitLabel={action === "approve" ? "Duyệt" : "Từ chối"}
      onCancel={() => {
        close();
        onCancel?.();
      }}
      onSubmit={() => decide(action === "approve")}
    >
      {subject && <p className="confirm-copy">{subject}</p>}
      {action === "approve" ? (
        <p className="confirm-copy">Xác nhận duyệt yêu cầu này?</p>
      ) : (
        <Field label="Lý do từ chối *">
          <textarea
            required
            minLength={5}
            maxLength={500}
            rows={3}
            value={reason}
            onChange={(e) => setReason(e.target.value)}
          />
        </Field>
      )}
    </ActionForm>
  );
  return (
    <div className="decision-actions">
      <ErrorBox message={error} />
      {embedded && action ? (
        form
      ) : (
        <div className="inline-actions">
          <button
            className="btn primary"
            disabled={busy}
            onClick={() =>
              embedded ? void approveInDialog() : setAction("approve")
            }
          >
            {busy ? "Đang duyệt…" : "Duyệt"}
          </button>
          <button
            className="btn secondary"
            disabled={busy}
            onClick={() => setAction("reject")}
          >
            Từ chối
          </button>
        </div>
      )}
      {!embedded && action && (
        <Modal
          title={action === "approve" ? "Xác nhận duyệt" : "Xác nhận từ chối"}
          onClose={close}
        >
          {form}
        </Modal>
      )}
    </div>
  );
}
