import { Link } from "react-router-dom";
import { ArrowUpRight } from "lucide-react";
import { date } from "../utils";
import type { Loan } from "../types";
import { Badge, Empty } from "./ui";
export default function LoanTable({
  loans,
  manage = false,
  onReview,
}: {
  loans: Loan[];
  manage?: boolean;
  onReview?: (loan: Loan) => void;
}) {
  return loans.length ? (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Phiếu / Tài sản</th>
            <th>{manage ? "Người mượn" : "Đơn vị chia sẻ"}</th>
            <th>Thời gian sử dụng</th>
            <th>Trạng thái</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {loans.map((n) => (
            <tr key={n.id}>
              <td>
                <Link className="table-title" to={`/loans/${n.id}`}>
                  {n.asset_name}
                </Link>
                <small>
                  PM-{String(n.id).padStart(4, "0")} — {n.category_name}
                </small>
              </td>
              <td>
                {manage ? n.borrower_name : n.asset_unit_name}
                {manage && <small>{n.borrower_unit_name}</small>}
              </td>
              <td>
                <div>{date(n.start_at)}</div>
                <small>đến {date(n.end_at)}</small>
              </td>
              <td>
                <Badge status={n.status} overdue={n.overdue} />
              </td>
              <td>
                {manage && n.status === "CHO_DUYET" && onReview && (
                  <button
                    className="btn small primary"
                    onClick={() => onReview(n)}
                  >
                    Xét duyệt
                  </button>
                )}
                <Link
                  className="icon-button"
                  aria-label={`Xem phiếu ${n.id}`}
                  to={`/loans/${n.id}`}
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
    <Empty text="Chưa có phiếu mượn phù hợp." />
  );
}
