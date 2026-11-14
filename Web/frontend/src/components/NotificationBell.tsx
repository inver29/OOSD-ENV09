import { useState } from "react";
import { Bell } from "lucide-react";
import { send } from "../api";
import { useData } from "../hooks";
import type { Page, WithdrawalNotice } from "../types";
import { date, errorText } from "../utils";
import { Empty, ErrorBox, Loading, Modal, Pagination } from "./ui";

export default function NotificationBell() {
  const [open, setOpen] = useState(false);
  const [page, setPage] = useState(1);
  const [reading, setReading] = useState<number | null>(null);
  const [readError, setReadError] = useState("");
  const { data, loading, error, reload } = useData<
    Page<WithdrawalNotice> & { unread: number }
  >(`/notifications?page=${page}`);

  async function markRead(id: number) {
    setReadError("");
    setReading(id);
    try {
      await send(`/notifications/${id}/read`);
      reload();
    } catch (e) {
      setReadError(errorText(e));
    } finally {
      setReading(null);
    }
  }

  return (
    <>
      <button
        type="button"
        className="icon-button notification-button"
        aria-label="Thông báo"
        aria-haspopup="dialog"
        aria-expanded={open}
        onClick={() => {
          setReadError("");
          setOpen(true);
          reload();
        }}
      >
        <Bell size={20} />
        {!!data?.unread && (
          <span
            className="notification-count"
            aria-label={`${data.unread} chưa đọc`}
          >
            {data.unread > 99 ? "99+" : data.unread}
          </span>
        )}
      </button>
      {open && (
        <Modal title="Thông báo" onClose={() => setOpen(false)}>
          <ErrorBox message={readError || error} />
          {loading && !data && <Loading />}
          {data?.total === 0 && <Empty text="Bạn chưa có thông báo." />}
          {!!data?.total && (
            <>
              <ul className="notification-list">
                {data.items.map((notice) => (
                  <li key={notice.id}>
                    <strong>{notice.asset_name}</strong>
                    <small>
                      Phiếu PM-{String(notice.loan_id).padStart(4, "0")} ·{" "}
                      {date(notice.created_at)}
                    </small>
                    <p>{notice.reason}. Phiếu mượn đã bị hủy.</p>
                    {!notice.read_at && (
                      <button
                        type="button"
                        className="btn secondary small"
                        disabled={reading !== null}
                        onClick={() => markRead(notice.id)}
                      >
                        Đánh dấu đã đọc
                      </button>
                    )}
                  </li>
                ))}
              </ul>
              {data.total > data.page_size && (
                <Pagination
                  page={page}
                  total={data.total}
                  size={data.page_size}
                  onChange={setPage}
                />
              )}
            </>
          )}
        </Modal>
      )}
    </>
  );
}
