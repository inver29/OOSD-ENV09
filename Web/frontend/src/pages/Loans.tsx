import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Search, RefreshCw } from "lucide-react";
import { query } from "../api";
import { useData, useDebouncedValue } from "../hooks";
import type { Loan, Page } from "../types";
import { label, loanStates, loanStageStates } from "../utils";
import { ErrorBox, Loading, PageHeader, Pagination } from "../components/ui";
import LoanTable from "../components/LoanTable";
import QuickReview from "../components/QuickReview";
export default function Loans({ manage = false }: { manage?: boolean }) {
  const [params, setParams] = useSearchParams();
  const queryStatus = params.get("status") || "";
  const oldStatuses: Record<string, string> = {
    DA_DUYET: "CHO_BAN_GIAO",
    DA_DONG: "DA_HOAN_TRA",
  };
  const requestedStatus = oldStatuses[queryStatus] ?? queryStatus;
  const status = loanStates.includes(requestedStatus) ? requestedStatus : "";
  const [search, setSearch] = useState(""),
    [page, setPage] = useState(1);
  const setStatus = (value: string) => {
    const next = new URLSearchParams(params);
    if (value) next.set("status", value);
    else next.delete("status");
    setParams(next, { replace: true });
    setPage(1);
  };
  const [review, setReview] = useState<Loan | null>(null);
  const q = useDebouncedValue(search.trim());
  const { data, loading, error, reload } = useData<Page<Loan>>(
    `/loans?${query({ scope: manage ? "manage" : "mine", status, q, page })}`,
  );
  return (
    <>
      <PageHeader
        eyebrow={manage ? "QUẢN LÝ TÀI SẢN" : "MƯỢN & HOÀN TRẢ"}
        title={manage ? "Xử lý mượn–trả" : "Phiếu mượn của tôi"}
        description={
          manage
            ? "Xử lý yêu cầu và xác nhận giao nhận cho tài sản của đơn vị."
            : "Theo dõi yêu cầu từ lúc đặt mượn đến khi hoàn trả."
        }
        action={
          <button className="btn secondary" onClick={reload}>
            <RefreshCw size={16} /> Làm mới
          </button>
        }
      />
      <section className="panel">
        {manage && (
          <div className="status-tabs" aria-label="Tiến độ mượn trả">
            {["", ...loanStageStates].map((value) => (
              <button
                key={value}
                className={status === value ? "active" : ""}
                onClick={() => {
                  setStatus(value);
                  setPage(1);
                }}
              >
                {value ? label(value) : "Tất cả"}
              </button>
            ))}
          </div>
        )}
        <div className="filters">
          <div className="search-box">
            <Search size={18} />
            <input
              aria-label="Tìm phiếu mượn"
              placeholder="Tìm theo tên tài sản…"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
            />
          </div>
          <select
            aria-label="Lọc trạng thái"
            value={status}
            onChange={(e) => {
              setStatus(e.target.value);
              setPage(1);
            }}
          >
            <option value="">Tất cả trạng thái</option>
            {loanStates.map((x) => (
              <option key={x} value={x}>
                {label(x)}
              </option>
            ))}
          </select>
        </div>
        <ErrorBox message={error} />
        {loading && !data ? (
          <Loading />
        ) : (
          <LoanTable
            loans={data?.items || []}
            manage={manage}
            onReview={setReview}
          />
        )}
        <Pagination page={page} total={data?.total || 0} onChange={setPage} />
      </section>
      {review && (
        <QuickReview
          loan={review}
          onClose={() => setReview(null)}
          onDone={() => {
            setReview(null);
            reload();
          }}
        />
      )}
    </>
  );
}
