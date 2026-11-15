import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { send } from "../api";
import { useAuth, useToast } from "../context";
import type { Asset, Loan } from "../types";
import { iso, label, localDate, needAlternatives } from "../utils";
import { ActionForm, Field, Modal } from "./ui";

export default function LoanRequest({
  asset,
  onClose,
}: {
  asset: Asset;
  onClose: () => void;
}) {
  const navigate = useNavigate(),
    toast = useToast(),
    { lookups } = useAuth();
  const [start, setStart] = useState(localDate(new Date(Date.now() + 3600000))),
    [end, setEnd] = useState(localDate(new Date(Date.now() + 86400000))),
    [purpose, setPurpose] = useState(""),
    [alternative, setAlternative] = useState("");
  const [requestId] = useState(() => crypto.randomUUID());
  return (
    <Modal title="Đặt mượn tài sản" onClose={onClose}>
      <p className="selected-asset-name">
        {asset.name} — {asset.unit_name}
      </p>
      <ActionForm
        submitLabel="Gửi yêu cầu"
        onCancel={onClose}
        onSubmit={async () => {
          const n = await send<Loan>("/loans", {
            asset_id: asset.id,
            start_at: iso(start),
            end_at: iso(end),
            purpose,
            request_id: requestId,
            new_need: {
              category_id: asset.category_id,
              purpose,
              start_at: iso(start),
              end_at: iso(end),
              alternative,
            },
          });
          toast("Đã gửi yêu cầu. Phiếu chờ duyệt chưa giữ lịch.");
          navigate(`/loans/${n.id}`);
        }}
      >
        <div className="form-grid">
          <Field label="Nhận từ *">
            <input
              required
              type="datetime-local"
              min={localDate()}
              value={start}
              onChange={(e) => setStart(e.target.value)}
            />
          </Field>
          <Field label="Trả trước *">
            <input
              required
              type="datetime-local"
              min={start}
              value={end}
              onChange={(e) => setEnd(e.target.value)}
            />
          </Field>
          <Field label="Mục đích sử dụng *" wide>
            <textarea
              required
              minLength={10}
              maxLength={1000}
              value={purpose}
              onChange={(e) => setPurpose(e.target.value)}
              rows={3}
            />
          </Field>
          <Field label="Nếu không mượn được, đơn vị sẽ… *" wide>
            <select
              required
              value={alternative}
              onChange={(e) => setAlternative(e.target.value)}
            >
              <option value="" disabled>
                Chọn phương án
              </option>
              {needAlternatives.map((x) => (
                <option key={x} value={x}>
                  {label(x)}
                </option>
              ))}
            </select>
          </Field>
        </div>
        <p className="form-caption">
          Mượn tối đa {lookups?.policy?.max_days || "—"} ngày, nhận trong{" "}
          {lookups?.policy?.pickup_hours || "—"} giờ từ lúc bắt đầu.
        </p>
      </ActionForm>
    </Modal>
  );
}
