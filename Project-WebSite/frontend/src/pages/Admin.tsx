import { useState } from "react";
import { Edit3, Plus, Search, Trash2 } from "lucide-react";
import { api, send } from "../api";
import { useAuth, useToast } from "../context";
import { useData, useDebouncedValue } from "../hooks";
import type { Catalog, Policy, User } from "../types";
import { date, iso, label, localDate } from "../utils";
import {
  ActionForm,
  Empty,
  ErrorBox,
  Field,
  Loading,
  Modal,
  PageHeader,
} from "../components/ui";
const catalogNames: Record<string, string> = {
  units: "Đơn vị",
  categories: "Loại tài sản",
  locations: "Địa điểm",
};
const searchPlaceholders: Record<string, string> = {
  users: "Tìm theo họ tên hoặc tên đăng nhập…",
  units: "Tìm theo tên đơn vị hoặc địa chỉ…",
  categories: "Tìm theo tên loại tài sản…",
  locations: "Tìm theo tên địa điểm, đơn vị hoặc mô tả…",
  policies: "Tìm theo tên chính sách…",
};
const policyStates: Record<string, string> = {
  current: "Đang áp dụng",
  scheduled: "Chưa đến hiệu lực",
  replaced: "Đã thay thế",
};
const emptyFilters = { search: "", unit: "", role: "", active: "", effect: "" };
const accountRoles = ["THANH_VIEN", "QUAN_LY", "QUAN_TRI"];
function searchText(value: string) {
  return value
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/đ/g, "d");
}

function UserEditor({
  user,
  onClose,
  onSaved,
}: {
  user?: User;
  onClose: () => void;
  onSaved: () => void;
}) {
  const { lookups } = useAuth();
  const [name, setName] = useState(user?.name || ""),
    [username, setUsername] = useState(user?.username || ""),
    [email, setEmail] = useState(user?.email || ""),
    [unit, setUnit] = useState(user?.unit_id || 0),
    [role, setRole] = useState(
      user ? (user.roles.length === 1 ? user.roles[0] : "") : "THANH_VIEN",
    ),
    [active, setActive] = useState(user?.active ?? true),
    [password, setPassword] = useState("");
  return (
    <Modal
      title={user ? "Cập nhật tài khoản" : "Tạo tài khoản"}
      onClose={onClose}
    >
      <ActionForm
        onCancel={onClose}
        onSubmit={async () => {
          await send(
            user ? `/admin/users/${user.id}` : "/admin/users",
            {
              name,
              username,
              email,
              unit_id: unit,
              roles: [role],
              active,
              password: password || null,
            },
            user ? "PUT" : "POST",
          );
          onSaved();
        }}
      >
        <div className="form-grid">
          <Field label="Họ tên *" wide>
            <input
              required
              minLength={2}
              maxLength={150}
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </Field>
          <Field label="Tên đăng nhập *">
            <input
              required
              minLength={3}
              maxLength={100}
              pattern="[a-zA-Z0-9_.-]+"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="off"
            />
          </Field>
          <Field label="Email *">
            <input
              required
              type="email"
              maxLength={254}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </Field>
          <Field label="Đơn vị *" wide>
            <select
              required
              value={unit}
              onChange={(e) => setUnit(+e.target.value)}
            >
              <option value={0} disabled>
                Chọn đơn vị
              </option>
              {lookups?.units
                .filter((u) => u.active)
                .map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.name}
                  </option>
                ))}
            </select>
          </Field>
          <Field
            label={
              user ? "Mật khẩu mới (để trống nếu giữ nguyên)" : "Mật khẩu *"
            }
            wide
          >
            <input
              required={!user}
              minLength={8}
              maxLength={128}
              type="password"
              autoComplete="new-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </Field>
          <Field label="Vai trò *" wide>
            <select
              required
              value={role}
              onChange={(e) => setRole(e.target.value)}
            >
              <option value="" disabled>
                Chọn vai trò
              </option>
              {accountRoles.map((value) => (
                <option key={value} value={value}>
                  {label(value)}
                </option>
              ))}
            </select>
          </Field>
          <label className="checkbox wide">
            <input
              type="checkbox"
              checked={active}
              onChange={(e) => setActive(e.target.checked)}
            />
            Cho phép tài khoản hoạt động
          </label>
        </div>
      </ActionForm>
    </Modal>
  );
}
function CatalogEditor({
  item,
  kind,
  onClose,
  onSaved,
}: {
  item?: Catalog;
  kind: string;
  onClose: () => void;
  onSaved: () => void;
}) {
  const { lookups } = useAuth();
  const [name, setName] = useState(item?.name || ""),
    [active, setActive] = useState(item?.active ?? true),
    [unit, setUnit] = useState(item?.unit_id || 0),
    [address, setAddress] = useState(item?.address || ""),
    [description, setDescription] = useState(item?.description || "");
  return (
    <Modal
      title={`${item ? "Cập nhật" : "Thêm"} ${catalogNames[kind].toLowerCase()}`}
      onClose={onClose}
    >
      <ActionForm
        onCancel={onClose}
        onSubmit={async () => {
          await send(
            `/admin/catalog/${kind}${item ? `/${item.id}` : ""}`,
            {
              name,
              active,
              address: kind === "units" ? address : null,
              unit_id: kind === "locations" ? unit : null,
              description: kind === "locations" ? description : null,
            },
            item ? "PUT" : "POST",
          );
          onSaved();
        }}
      >
        <div className="form-grid">
          <Field label="Tên *" wide>
            <input
              required
              minLength={2}
              maxLength={150}
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </Field>
          {kind === "units" && (
            <Field label="Địa chỉ cụ thể *" wide>
              <textarea
                required
                minLength={8}
                maxLength={300}
                rows={3}
                value={address}
                onChange={(e) => setAddress(e.target.value)}
                placeholder="Số nhà, đường, phường/xã, tỉnh/thành phố"
              />
            </Field>
          )}
          {kind === "locations" && (
            <>
              <Field label="Đơn vị *" wide>
                <select
                  required
                  value={unit}
                  onChange={(e) => setUnit(+e.target.value)}
                >
                  <option value={0} disabled>
                    Chọn đơn vị
                  </option>
                  {lookups?.units
                    .filter((x) => x.active)
                    .map((u) => (
                      <option key={u.id} value={u.id}>
                        {u.name}
                      </option>
                    ))}
                </select>
              </Field>
              <Field label="Mô tả" wide>
                <textarea
                  maxLength={500}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                />
              </Field>
            </>
          )}
          <label className="checkbox wide">
            <input
              type="checkbox"
              checked={active}
              onChange={(e) => setActive(e.target.checked)}
            />
            Đang hoạt động
          </label>
        </div>
      </ActionForm>
    </Modal>
  );
}
function PolicyEditor({
  item,
  onClose,
  onSaved,
}: {
  item?: Policy;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [name, setName] = useState(item?.name || ""),
    [max, setMax] = useState(item?.max_days || 14),
    [buffer, setBuffer] = useState(item?.buffer_hours ?? 2),
    [pickup, setPickup] = useState(item?.pickup_hours || 24),
    [effective, setEffective] = useState(localDate(item?.effective_from));
  return (
    <Modal
      title={item ? "Sửa chính sách chưa dùng" : "Thêm chính sách mượn"}
      onClose={onClose}
    >
      <ActionForm
        onCancel={onClose}
        onSubmit={async () => {
          await send(
            `/admin/policies${item ? `/${item.id}` : ""}`,
            {
              name,
              max_days: max,
              buffer_hours: buffer,
              pickup_hours: pickup,
              effective_from: iso(effective),
            },
            item ? "PUT" : "POST",
          );
          onSaved();
        }}
      >
        <div className="form-grid">
          <Field label="Tên chính sách *" wide>
            <input
              required
              minLength={2}
              maxLength={150}
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </Field>
          <Field label="Số ngày mượn tối đa *">
            <input
              required
              type="number"
              min={1}
              max={365}
              value={max}
              onChange={(e) => setMax(+e.target.value)}
            />
          </Field>
          <Field label="Giờ dự phòng sau trả *">
            <input
              required
              type="number"
              min={0}
              max={168}
              value={buffer}
              onChange={(e) => setBuffer(+e.target.value)}
            />
          </Field>
          <Field label="Giờ chờ đến nhận *">
            <input
              required
              type="number"
              min={1}
              max={168}
              value={pickup}
              onChange={(e) => setPickup(+e.target.value)}
            />
          </Field>
          <Field label="Hiệu lực từ *">
            <input
              required
              type="datetime-local"
              value={effective}
              onChange={(e) => setEffective(e.target.value)}
            />
          </Field>
        </div>
      </ActionForm>
    </Modal>
  );
}
export default function Admin() {
  const { lookups, reloadLookups } = useAuth(),
    toast = useToast();
  const [tab, setTab] = useState("users"),
    [edit, setEdit] = useState<User | Catalog | Policy | undefined>(),
    [open, setOpen] = useState(false),
    [remove, setRemove] = useState<Catalog | Policy | null>(null);
  const [filters, setFilters] = useState(emptyFilters);
  const debouncedSearch = useDebouncedValue(filters.search.trim());
  const q = filters.search.trim() ? searchText(debouncedSearch) : "";
  const changeFilter = (key: keyof typeof emptyFilters, value: string) =>
    setFilters((current) => ({ ...current, [key]: value }));
  const {
    data: users,
    loading,
    error,
    reload,
  } = useData<User[]>("/admin/users");
  const {
    data: policies,
    loading: policiesLoading,
    error: policiesError,
    reload: reloadPolicies,
  } = useData<Policy[]>("/admin/policies");
  const saved = async () => {
    setOpen(false);
    setEdit(undefined);
    reload();
    reloadPolicies();
    await reloadLookups();
    toast("Đã lưu thay đổi.");
  };
  const catalog = (lookups?.[tab as "units" | "locations" | "categories"] ||
    []) as Catalog[];
  const matchesSearch = (...values: (string | null | undefined)[]) =>
    !q || searchText(values.filter(Boolean).join(" ")).includes(q);
  const matchesActive = (active: boolean) =>
    !filters.active || String(active) === filters.active;
  const filteredUsers = (users || []).filter(
    (u) =>
      matchesSearch(u.name, u.username) &&
      matchesActive(u.active) &&
      (!filters.unit || String(u.unit_id) === filters.unit) &&
      (!filters.role || u.roles.includes(filters.role)),
  );
  const filteredCatalog = catalog.filter(
    (c) =>
      matchesSearch(
        c.name,
        c.address,
        c.description,
        tab === "locations"
          ? lookups?.units.find((u) => u.id === c.unit_id)?.name
          : "",
      ) &&
      matchesActive(c.active) &&
      (!filters.unit || String(c.unit_id) === filters.unit),
  );
  const now = Date.now();
  const currentPolicy = (policies || []).reduce<Policy | null>(
    (current, p) =>
      new Date(p.effective_from).getTime() <= now &&
      (!current ||
        new Date(p.effective_from) > new Date(current.effective_from))
        ? p
        : current,
    null,
  );
  const policyState = (p: Policy) =>
    new Date(p.effective_from).getTime() > now
      ? "scheduled"
      : p.id === currentPolicy?.id
        ? "current"
        : "replaced";
  const filteredPolicies = (policies || []).filter(
    (p) =>
      matchesSearch(p.name) &&
      (!filters.effect || policyState(p) === filters.effect),
  );
  const resultCount =
    tab === "users"
      ? filteredUsers.length
      : tab === "policies"
        ? filteredPolicies.length
        : filteredCatalog.length;
  const totalCount =
    tab === "users"
      ? users?.length || 0
      : tab === "policies"
        ? policies?.length || 0
        : catalog.length;
  const initialLoading =
    tab === "users"
      ? loading && !users
      : tab === "policies"
        ? policiesLoading && !policies
        : !lookups;
  const hasFilters = Object.values(filters).some(Boolean);
  return (
    <>
      <PageHeader
        eyebrow="QUẢN TRỊ HỆ THỐNG"
        title="Tài khoản & cấu hình"
        description="Quản lý quyền truy cập, danh mục dùng chung và chính sách mượn."
        action={
          <button
            className="btn primary"
            onClick={() => {
              setEdit(undefined);
              setOpen(true);
            }}
          >
            <Plus size={17} />{" "}
            {tab === "users"
              ? "Tạo tài khoản"
              : tab === "policies"
                ? "Thêm chính sách"
                : `Thêm ${catalogNames[tab].toLowerCase()}`}
          </button>
        }
      />
      <div className="page-tabs">
        {[
          ["users", "Tài khoản"],
          ["units", "Đơn vị"],
          ["categories", "Loại tài sản"],
          ["locations", "Địa điểm"],
          ["policies", "Chính sách mượn"],
        ].map(([k, v]) => (
          <button
            key={k}
            className={tab === k ? "active" : ""}
            onClick={() => {
              setTab(k);
              setFilters(emptyFilters);
            }}
          >
            {v}
          </button>
        ))}
      </div>
      <ErrorBox
        message={
          tab === "users" ? error : tab === "policies" ? policiesError : ""
        }
      />
      <section className="panel admin-panel">
        <div className="filters admin-filters">
          <div className="search-box">
            <Search size={18} />
            <input
              type="search"
              aria-label="Tìm kiếm quản trị"
              placeholder={searchPlaceholders[tab]}
              value={filters.search}
              onChange={(e) => changeFilter("search", e.target.value)}
            />
          </div>
          {(tab === "users" || tab === "locations") && (
            <select
              className="admin-unit-filter"
              aria-label="Lọc đơn vị quản trị"
              value={filters.unit}
              onChange={(e) => changeFilter("unit", e.target.value)}
            >
              <option value="">Mọi đơn vị</option>
              {lookups?.units.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.name}
                </option>
              ))}
            </select>
          )}
          {tab === "users" && (
            <select
              aria-label="Lọc vai trò quản trị"
              value={filters.role}
              onChange={(e) => changeFilter("role", e.target.value)}
            >
              <option value="">Mọi vai trò</option>
              {accountRoles.map((role) => (
                <option key={role} value={role}>
                  {label(role)}
                </option>
              ))}
            </select>
          )}
          {tab === "policies" ? (
            <select
              className="admin-policy-filter"
              aria-label="Lọc hiệu lực chính sách"
              value={filters.effect}
              onChange={(e) => changeFilter("effect", e.target.value)}
            >
              <option value="">Mọi hiệu lực</option>
              {Object.entries(policyStates).map(([value, name]) => (
                <option key={value} value={value}>
                  {name}
                </option>
              ))}
            </select>
          ) : (
            <select
              aria-label="Lọc trạng thái quản trị"
              value={filters.active}
              onChange={(e) => changeFilter("active", e.target.value)}
            >
              <option value="">Mọi trạng thái</option>
              <option value="true">Hoạt động</option>
              <option value="false">
                {tab === "users" ? "Đã khóa" : "Ngừng hoạt động"}
              </option>
            </select>
          )}
        </div>
        {initialLoading ? (
          <Loading />
        ) : resultCount === 0 ? (
          <Empty
            text={hasFilters ? "Không có kết quả phù hợp." : "Chưa có dữ liệu."}
          />
        ) : tab === "users" ? (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Tài khoản</th>
                  <th>Đơn vị</th>
                  <th>Vai trò</th>
                  <th>Trạng thái</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {filteredUsers.map((u) => (
                  <tr key={u.id}>
                    <td>
                      <strong>{u.name}</strong>
                      <small>{u.username}</small>
                    </td>
                    <td>{u.unit_name}</td>
                    <td>
                      <div className="role-chips">
                        {u.roles.map((r) => (
                          <span className="pill" key={r}>
                            {label(r)}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td>
                      <span className={`pill ${u.active ? "positive" : ""}`}>
                        {u.active ? "Hoạt động" : "Đã khóa"}
                      </span>
                    </td>
                    <td>
                      <button
                        className="icon-button"
                        aria-label={`Sửa tài khoản ${u.username}`}
                        onClick={() => {
                          setEdit(u);
                          setOpen(true);
                        }}
                      >
                        <Edit3 size={17} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : tab === "policies" ? (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Chính sách</th>
                  <th>Tối đa</th>
                  <th>Giờ dự phòng</th>
                  <th>Giờ nhận</th>
                  <th>Hiệu lực từ</th>
                  <th>Hiệu lực</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {filteredPolicies.map((p) => (
                  <tr key={p.id}>
                    <td>
                      <strong>{p.name}</strong>
                    </td>
                    <td>{p.max_days} ngày</td>
                    <td>{p.buffer_hours} giờ</td>
                    <td>{p.pickup_hours} giờ</td>
                    <td>{date(p.effective_from)}</td>
                    <td>
                      <span
                        className={`pill ${policyState(p) === "current" ? "positive" : ""}`}
                      >
                        {policyStates[policyState(p)]}
                      </span>
                    </td>
                    <td>
                      <div className="inline-actions compact">
                        <button
                          className="icon-button"
                          aria-label={`Sửa ${p.name}`}
                          onClick={() => {
                            setEdit(p);
                            setOpen(true);
                          }}
                        >
                          <Edit3 size={17} />
                        </button>
                        <button
                          className="icon-button"
                          aria-label={`Xóa ${p.name}`}
                          onClick={() => setRemove(p)}
                        >
                          <Trash2 size={17} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>{catalogNames[tab]}</th>
                  {tab === "units" && <th>Địa chỉ cụ thể</th>}
                  {tab === "locations" && <th>Đơn vị / Mô tả</th>}
                  <th>Trạng thái</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {filteredCatalog.map((c) => (
                  <tr key={c.id}>
                    <td>
                      <strong>{c.name}</strong>
                    </td>
                    {tab === "units" && <td>{c.address || "Chưa cập nhật"}</td>}
                    {tab === "locations" && (
                      <td>
                        {lookups?.units.find((u) => u.id === c.unit_id)?.name}
                        <small>{c.description}</small>
                      </td>
                    )}
                    <td>
                      <span className={`pill ${c.active ? "positive" : ""}`}>
                        {c.active ? "Hoạt động" : "Ngừng hoạt động"}
                      </span>
                    </td>
                    <td>
                      <div className="inline-actions compact">
                        <button
                          className="icon-button"
                          aria-label={`Sửa ${c.name}`}
                          onClick={() => {
                            setEdit(c);
                            setOpen(true);
                          }}
                        >
                          <Edit3 size={17} />
                        </button>
                        <button
                          className="icon-button"
                          aria-label={`Xóa ${c.name}`}
                          onClick={() => setRemove(c)}
                        >
                          <Trash2 size={17} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {!initialLoading && (
          <div className="admin-results">
            <span role="status">
              {resultCount} / {totalCount} kết quả
            </span>
            {hasFilters && (
              <button
                className="btn secondary small"
                onClick={() => setFilters(emptyFilters)}
              >
                Xóa bộ lọc
              </button>
            )}
          </div>
        )}
      </section>
      {open &&
        (tab === "users" ? (
          <UserEditor
            user={edit as User | undefined}
            onClose={() => setOpen(false)}
            onSaved={saved}
          />
        ) : tab === "policies" ? (
          <PolicyEditor
            item={edit as Policy | undefined}
            onClose={() => setOpen(false)}
            onSaved={saved}
          />
        ) : (
          <CatalogEditor
            kind={tab}
            item={edit as Catalog | undefined}
            onClose={() => setOpen(false)}
            onSaved={saved}
          />
        ))}
      {remove && (
        <Modal title="Xóa dữ liệu chưa sử dụng" onClose={() => setRemove(null)}>
          <ActionForm
            submitLabel="Xóa mục này"
            onCancel={() => setRemove(null)}
            onSubmit={async () => {
              await api(
                tab === "policies"
                  ? `/admin/policies/${remove.id}`
                  : `/admin/catalog/${tab}/${remove.id}`,
                { method: "DELETE" },
              );
              setRemove(null);
              await saved();
            }}
          >
            <p className="confirm-copy">
              Xóa “{remove.name}”? Dữ liệu đã được tham chiếu sẽ được giữ lại.
            </p>
          </ActionForm>
        </Modal>
      )}
    </>
  );
}
