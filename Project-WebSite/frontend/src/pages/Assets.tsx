import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  ArrowUpRight,
  MapPin,
  Plus,
  Search,
  SlidersHorizontal,
} from "lucide-react";
import { query } from "../api";
import { useAuth } from "../context";
import { useData, useDebouncedValue } from "../hooks";
import type { Asset, Page } from "../types";
import { iso, label } from "../utils";
import {
  Badge,
  DeviceArt,
  Empty,
  ErrorBox,
  Loading,
  PageHeader,
  Pagination,
} from "../components/ui";
import AssetForm from "../components/AssetForm";
import QuickReview from "../components/QuickReview";
export default function Assets({ own = false }: { own?: boolean }) {
  const { lookups, user } = useAuth(),
    navigate = useNavigate();
  const [search, setSearch] = useState(""),
    [category, setCategory] = useState(""),
    [unit, setUnit] = useState(""),
    [status, setStatus] = useState(""),
    [page, setPage] = useState(1),
    [advanced, setAdvanced] = useState(false),
    [start, setStart] = useState(""),
    [end, setEnd] = useState(""),
    [create, setCreate] = useState(false);
  const [review, setReview] = useState<Asset | null>(null);
  const q = useDebouncedValue(search.trim());
  const from = useDebouncedValue(start),
    until = useDebouncedValue(end);
  const validPeriod = Boolean(
    from && until && new Date(until) > new Date(from),
  );
  const period = validPeriod ? { start: iso(from), end: iso(until) } : {};

  const { data, loading, error, reload } = useData<Page<Asset>>(
    `/assets?${query({ scope: own ? "own" : "shared", q, category_id: category, unit_id: unit, status, page, ...period })}`,
  );
  return (
    <>
      <PageHeader
        eyebrow={own ? "TÀI SẢN NỘI BỘ" : "KHÁM PHÁ & KẾT NỐI"}
        title={own ? "Tài sản đơn vị" : "Tìm tài sản bạn cần"}
        description={
          own
            ? "Thêm tài sản, xét duyệt chia sẻ và theo dõi vòng đời trong đơn vị."
            : "Mượn thiết bị sẵn có từ các đơn vị trong cùng tổ chức."
        }
        action={
          own && (
            <button className="btn primary" onClick={() => setCreate(true)}>
              <Plus size={17} /> Đăng ký tài sản
            </button>
          )
        }
      />
      <div className="catalog-toolbar">
        <div className="search-box">
          <Search size={19} />
          <input
            aria-label="Tìm tài sản"
            placeholder="Bạn đang tìm thiết bị gì?"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
          />
        </div>
        <button
          className={`btn ${advanced ? "primary" : "secondary"}`}
          onClick={() => setAdvanced(!advanced)}
        >
          <SlidersHorizontal size={17} /> Lọc theo lịch
        </button>
      </div>
      <div className="catalog-filters">
        <div className="category-tabs">
          <button
            className={!category ? "active" : ""}
            onClick={() => {
              setCategory("");
              setPage(1);
            }}
          >
            Tất cả
          </button>
          {lookups?.categories
            .filter((c) => c.active)
            .map((c) => (
              <button
                className={category === String(c.id) ? "active" : ""}
                key={c.id}
                onClick={() => {
                  setCategory(String(c.id));
                  setPage(1);
                }}
              >
                {c.name}
              </button>
            ))}
        </div>
        {own ? (
          <select
            aria-label="Lọc tình trạng tài sản"
            value={status}
            onChange={(e) => {
              setStatus(e.target.value);
              setPage(1);
            }}
          >
            <option value="">Mọi trạng thái</option>
            {[
              "CHO_DUYET",
              "TU_CHOI",
              "CHO_CHIA_SE",
              "CHO_BAN_GIAO",
              "DA_DUOC_MUON",
              "BAO_TRI",
              "CHO_THU_HOI",
            ].map((s) => (
              <option key={s} value={s}>
                {label(s)}
              </option>
            ))}
          </select>
        ) : (
          <select
            aria-label="Lọc đơn vị"
            value={unit}
            onChange={(e) => {
              setUnit(e.target.value);
              setPage(1);
            }}
          >
            <option value="">Mọi đơn vị</option>
            {lookups?.units
              .filter((x) => x.active)
              .map((x) => (
                <option key={x.id} value={x.id}>
                  {x.name}
                </option>
              ))}
          </select>
        )}
      </div>
      {advanced && (
        <div className="period-filter panel">
          <label>
            Từ{" "}
            <input
              aria-label="Lọc lịch từ"
              type="datetime-local"
              value={start}
              onChange={(e) => {
                setStart(e.target.value);
                setPage(1);
              }}
            />
          </label>
          <label>
            Đến{" "}
            <input
              aria-label="Lọc lịch đến"
              type="datetime-local"
              min={start}
              value={end}
              onChange={(e) => {
                setEnd(e.target.value);
                setPage(1);
              }}
            />
          </label>
          <button
            type="button"
            className="btn secondary small"
            onClick={() => {
              setStart("");
              setEnd("");
              setPage(1);
            }}
          >
            Bỏ lọc lịch
          </button>
          {start && end && new Date(end) <= new Date(start) && (
            <span className="error-text">
              Thời gian kết thúc phải sau thời gian bắt đầu.
            </span>
          )}
        </div>
      )}
      <ErrorBox message={error} />
      {loading && !data ? (
        <Loading />
      ) : data?.items.length ? (
        <div className="asset-grid">
          {data.items.map((a) => (
            <article className="asset-card" key={a.id}>
              <Link
                className="asset-card-link"
                to={`/${own ? "owned" : "assets"}/${a.id}`}
              >
                <div className="asset-card-art">
                  <DeviceArt
                    category={a.category_name}
                    name={a.name}
                    image={a.image_path}
                  />
                  <Badge status={a.status} />
                </div>
                <div className="asset-card-body">
                  <span className="asset-category">{a.category_name}</span>
                  <h2>{a.name}</h2>
                  <p>{a.description || a.condition}</p>
                  <div className="asset-card-footer">
                    <span>
                      <MapPin size={14} />
                      {a.unit_name.replace("Chi nhánh ", "")}
                    </span>
                    <ArrowUpRight size={18} />
                  </div>
                </div>
              </Link>
              {own &&
                a.unit_id === user?.unit_id &&
                user.roles.includes("QUAN_LY") &&
                a.status === "CHO_DUYET" && (
                  <div className="card-actions">
                    <button
                      className="btn small primary"
                      onClick={() => setReview(a)}
                    >
                      Xét duyệt tài sản
                    </button>
                  </div>
                )}
            </article>
          ))}
        </div>
      ) : (
        <section className="panel">
          <Empty text="Chưa có tài sản phù hợp với bộ lọc." />
        </section>
      )}
      <Pagination page={page} total={data?.total || 0} onChange={setPage} />
      {create && (
        <AssetForm
          onClose={() => setCreate(false)}
          onSaved={(a) => navigate(`/owned/${a.id}`)}
        />
      )}
      {review && (
        <QuickReview
          asset={review}
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
