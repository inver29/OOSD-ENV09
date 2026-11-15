import { useState } from "react";
import { Link } from "react-router-dom";
import { ArrowUpRight, Search } from "lucide-react";
import { query } from "../api";
import { useData, useDebouncedValue } from "../hooks";
import type { Need, Page } from "../types";
import { date, label } from "../utils";
import {
  Badge,
  Empty,
  ErrorBox,
  Loading,
  PageHeader,
  Pagination,
} from "../components/ui";
export default function Needs({ manage = false }: { manage?: boolean }) {
  const [status, setStatus] = useState(""),
    [search, setSearch] = useState(""),
    [page, setPage] = useState(1);
  const q = useDebouncedValue(search.trim());
  const { data, loading, error } = useData<Page<Need>>(
    `/needs?${query({ scope: manage ? "manage" : "mine", status, q, page })}`,
  );
  return (
    <>
      <PageHeader
        eyebrow="ĐÁNH GIÁ HIỆU QUẢ TÁI SỬ DỤNG"
        title={manage ? "Xác minh nhu cầu" : "Nhu cầu sử dụng"}
        description={
          manage
            ? "Đối chiếu dự định mua và kết quả sử dụng của đơn vị."
            : "Tự động ghi nhận từ các lượt mượn đã hoàn trả."
        }
      />
      <section className="panel">
        <div className="filters">
          <div className="search-box">
            <Search size={18} />
            <input
              aria-label="Tìm nhu cầu"
              placeholder="Tìm theo mục đích sử dụng…"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
            />
          </div>
          <select
            aria-label="Trạng thái nhu cầu"
            value={status}
            onChange={(e) => {
              setStatus(e.target.value);
              setPage(1);
            }}
          >
            <option value="">Mọi trạng thái</option>
            {["CHO_XAC_MINH", "DA_XAC_MINH", "TU_CHOI"].map((x) => (
              <option key={x} value={x}>
                {label(x)}
              </option>
            ))}
          </select>
        </div>
        <ErrorBox message={error} />
        {loading && !data ? (
          <Loading />
        ) : data?.items.length ? (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Nhu cầu</th>
                  <th>{manage ? "Người lập" : "Loại tài sản"}</th>
                  <th>Kỳ sử dụng</th>
                  <th>Phương án ban đầu</th>
                  <th>Trạng thái</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {data.items.map((n) => (
                  <tr key={n.id}>
                    <td>
                      <Link className="table-title" to={`/needs/${n.id}`}>
                        {n.purpose}
                      </Link>
                      <small>NC-{n.id}</small>
                    </td>
                    <td>{manage ? n.creator_name : n.category_name}</td>
                    <td>
                      {date(n.start_at, false)}
                      <small>đến {date(n.end_at, false)}</small>
                    </td>
                    <td>{label(n.alternative)}</td>
                    <td>
                      {n.purchased === null ? (
                        <span className="pill">Chưa khai báo</span>
                      ) : (
                        <Badge status={n.status} />
                      )}
                    </td>
                    <td>
                      <Link
                        className="icon-button"
                        aria-label={`Xem nhu cầu ${n.id}`}
                        to={`/needs/${n.id}`}
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
          <Empty text="Chưa có nhu cầu phù hợp." />
        )}
        <Pagination page={page} total={data?.total || 0} onChange={setPage} />
      </section>
    </>
  );
}
