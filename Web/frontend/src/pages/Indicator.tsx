import { useState } from "react";
import { Link } from "react-router-dom";
import { ArrowUpRight, Download, Leaf } from "lucide-react";
import { query } from "../api";
import { useAuth } from "../context";
import { useData, useDebouncedValue } from "../hooks";
import type { Indicator as IndicatorData } from "../types";
import { date } from "../utils";
import { Empty, ErrorBox, Loading, PageHeader } from "../components/ui";
export default function Indicator() {
  const { lookups } = useAuth();
  const monthInVietnam = new Date(Date.now() + 7 * 60 * 60 * 1000);
  const monthStart = (offset: number) =>
    new Date(
      Date.UTC(
        monthInVietnam.getUTCFullYear(),
        monthInVietnam.getUTCMonth() + offset,
        1,
      ),
    )
      .toISOString()
      .slice(0, 10);
  const [start, setStart] = useState(() => monthStart(-1)),
    [end, setEnd] = useState(() => monthStart(1)),
    [category, setCategory] = useState("");
  const from = useDebouncedValue(start),
    until = useDebouncedValue(end);
  const valid = Boolean(from && until && until > from);
  const { data, loading, error } = useData<IndicatorData>(
    valid
      ? `/reports/avoidance?${query({ start: `${from}T00:00:00+07:00`, end: `${until}T00:00:00+07:00`, category_id: category })}`
      : null,
  );
  function exportCsv() {
    if (!data) return;
    const rows = [
      [
        "Ma nhu cau",
        "Muc dich",
        "Loai tai san",
        "Ket thuc",
        "Tranh mua moi",
        "Ly do",
      ],
      ...data.rows.map((r) => [
        String(r.id),
        r.purpose,
        r.category_name,
        date(r.end_at, true, "Asia/Ho_Chi_Minh"),
        r.avoided ? "Co" : "Khong",
        r.reason,
      ]),
    ];
    const csv =
      "\uFEFF" +
      rows
        .map((r) =>
          r
            .map(
              (v) =>
                '"' +
                (/^[=+\-@\t\r]/.test(v) ? "'" : "") +
                v.replaceAll('"', '""') +
                '"',
            )
            .join(","),
        )
        .join("\r\n");
    const url = URL.createObjectURL(
      new Blob([csv], { type: "text/csv;charset=utf-8;" }),
    );
    const a = document.createElement("a");
    a.href = url;
    a.download = "ENV09_ChiSoTranhMuaMoi.csv";
    a.click();
    URL.revokeObjectURL(url);
  }
  return (
    <>
      <PageHeader
        eyebrow="GIÁ TRỊ TÁI SỬ DỤNG"
        title="Chỉ số tránh mua mới"
        description="Đánh giá các lượt mượn đã hoàn trả và xác minh, mỗi nhu cầu tính một lần."
        action={
          <button
            className="btn secondary"
            disabled={!valid || loading || !data}
            onClick={exportCsv}
          >
            <Download size={17} /> Xuất CSV
          </button>
        }
      />
      <div className="period-filter panel">
        <label>
          Từ ngày{" "}
          <input
            required
            type="date"
            value={start}
            onChange={(e) => setStart(e.target.value)}
          />
        </label>
        <label>
          Đến trước ngày{" "}
          <input
            required
            min={start}
            type="date"
            value={end}
            onChange={(e) => setEnd(e.target.value)}
          />
        </label>
        <select
          aria-label="Loại tài sản"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
        >
          <option value="">Mọi loại tài sản</option>
          {lookups?.categories.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
      </div>
      {!valid && (
        <ErrorBox message="Chọn đủ thời gian; ngày kết thúc phải sau ngày bắt đầu." />
      )}
      <ErrorBox message={error} />
      {loading && !data ? (
        <Loading />
      ) : (
        valid &&
        data && (
          <>
            <div className="indicator-grid">
              <div className="indicator-main">
                <Leaf size={28} />
                <span>Tỷ lệ tránh mua mới</span>
                <strong>{data.rate === null ? "—" : `${data.rate}%`}</strong>
                <p>
                  {data.total === 0
                    ? "Chưa có nhu cầu đủ điều kiện trong kỳ."
                    : `${data.avoided} / ${data.total} nhu cầu đã xác minh`}
                </p>
              </div>
              <div className="panel indicator-number">
                <span>Nhu cầu dự định mua đã xác minh (D)</span>
                <strong>{data.total}</strong>
                <small>{data.unit_name}</small>
              </div>
              <div className="panel indicator-number">
                <span>Nhu cầu tránh được mua mới (A)</span>
                <strong>{data.avoided}</strong>
                <small>Đã trả, đáp ứng mục đích, không mua mới</small>
              </div>
            </div>
            <section className="panel">
              <div className="panel-heading">
                <h2>Nhu cầu được đối chiếu</h2>
                <span className="muted">
                  Ngày kết thúc nhu cầu · Giờ Việt Nam
                </span>
              </div>
              {data.rows.length ? (
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Nhu cầu</th>
                        <th>Người lập</th>
                        <th>Kết quả</th>
                        <th>Lý do</th>
                        <th />
                      </tr>
                    </thead>
                    <tbody>
                      {data.rows.map((r) => (
                        <tr key={r.id}>
                          <td>
                            <Link className="table-title" to={`/needs/${r.id}`}>
                              {r.purpose}
                            </Link>
                            <small>
                              NC-{r.id} — {r.category_name}
                            </small>
                          </td>
                          <td>{r.creator_name}</td>
                          <td>
                            <span
                              className={`pill ${r.avoided ? "positive" : ""}`}
                            >
                              {r.avoided ? "Tránh mua mới" : "Chưa đạt"}
                            </span>
                          </td>
                          <td>{r.reason}</td>
                          <td>
                            <Link
                              to={`/needs/${r.id}`}
                              className="icon-button"
                              aria-label={`Xem nhu cầu ${r.id}`}
                            >
                              <ArrowUpRight size={18} />
                            </Link>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <Empty text="Không có nhu cầu đã xác minh dự định mua trong kỳ." />
              )}
            </section>
            <section className="panel assumptions">
              <h2>Cách tính & giả định</h2>
              <p>
                <strong>R = A / D × 100%</strong>. Khi D = 0, không tính tỷ lệ.
              </p>
              <ul>
                {data.assumptions.map((s) => (
                  <li key={s}>{s}</li>
                ))}
              </ul>
            </section>
          </>
        )
      )}
    </>
  );
}
