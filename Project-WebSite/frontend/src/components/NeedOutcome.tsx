import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { send } from "../api";
import { useAuth, useToast } from "../context";
import type { Need } from "../types";
import { date, label } from "../utils";
import { ActionForm, Badge, DataItem, Field } from "./ui";

export default function NeedOutcome({
  need,
  onDone,
}: {
  need: Need;
  onDone: () => void;
}) {
  const { user } = useAuth(),
    toast = useToast();
  const [purchased, setPurchased] = useState(
    need.purchased === null ? "" : String(need.purchased),
  );
  useEffect(() => {
    setPurchased(need.purchased === null ? "" : String(need.purchased));
  }, [need.purchased]);
  return (
    <section className="panel detail-panel">
      <div className="panel-heading">
        <h2>Nhu cầu & kết quả sử dụng</h2>
        <Badge status={need.status} />
      </div>
      <p className="pre-line">{need.purpose}</p>
      <div className="data-grid">
        <DataItem title="Phương án ban đầu">{label(need.alternative)}</DataItem>
        <DataItem title="Kết thúc kỳ sử dụng">{date(need.end_at)}</DataItem>
      </div>
      {need.creator_id === user?.id ? (
        <ActionForm
          submitLabel="Lưu kết quả"
          onSubmit={async () => {
            await send(`/needs/${need.id}/outcome`, {
              purchased: purchased === "" ? null : purchased === "true",
            });
            toast(
              purchased === ""
                ? "Đã lưu trạng thái Chưa xác định."
                : "Đã lưu kết quả mua mới.",
            );
            onDone();
          }}
        >
          <Field label="Đơn vị có mua mới cho nhu cầu này không?">
            <select
              value={purchased}
              onChange={(e) => setPurchased(e.target.value)}
            >
              <option value="">Chưa xác định</option>
              <option value="false">Không mua mới</option>
              <option value="true">Có mua mới</option>
            </select>
          </Field>
        </ActionForm>
      ) : (
        <DataItem title="Kết quả mua mới">
          {need.purchased === null
            ? "Chưa khai báo"
            : need.purchased
              ? "Đã mua mới"
              : "Không mua mới"}
        </DataItem>
      )}
      <Link className="text-link" to={`/needs/${need.id}`}>
        Xem nhu cầu và kết quả xác minh
      </Link>
    </section>
  );
}
