import { useState } from "react";
import {
  BrowserRouter,
  Link,
  NavLink,
  Navigate,
  Outlet,
  Route,
  Routes,
  useLocation,
  useNavigate,
} from "react-router-dom";
import {
  ArrowUpRight,
  Boxes,
  ChartNoAxesCombined,
  ChevronDown,
  ClipboardList,
  LayoutDashboard,
  Leaf,
  LogOut,
  Menu,
  Search,
  Settings,
  ShieldCheck,
  X,
} from "lucide-react";
import { AuthProvider, ToastProvider, useAuth } from "./context";
import { ActionForm, ErrorBox, Field, Loading, Modal } from "./components/ui";
import { send } from "./api";
import { label } from "./utils";
import Dashboard from "./pages/Dashboard";
import Assets from "./pages/Assets";
import AssetDetail from "./pages/AssetDetail";
import Loans from "./pages/Loans";
import LoanDetail from "./pages/LoanDetail";
import NeedDetail from "./pages/NeedDetail";
import { Borrowing, Effectiveness } from "./pages/Workspaces";
import Admin from "./pages/Admin";
import NotificationBell from "./components/NotificationBell";

function Login() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [username, setUsername] = useState(""),
    [password, setPassword] = useState("");
  return (
    <div className="login-page">
      <div className="login-story">
        <Link className="brand" to="/">
          <span className="brand-icon">
            <Leaf />
          </span>
          ENV<span>09</span>
        </Link>
        <div>
          <div className="eyebrow">CHIA SẺ TRONG CÙNG TỔ CHỨC</div>
          <h1>
            Tài sản sẵn có.
            <br />
            Giá trị tiếp nối.
          </h1>
          <p>
            Kết nối thiết bị đang nhàn rỗi với nơi cần sử dụng. Mượn đúng lúc,
            dùng hiệu quả, giảm mua mới.
          </p>
          <div className="login-visual">
            <div className="visual-box">
              <Boxes size={38} strokeWidth={1.6} />
            </div>
            <div className="login-visual-copy">
              <strong>Luân chuyển thiết bị nội bộ</strong>
              <span>Tra cứu nhanh, đặt lịch rõ ràng, bàn giao minh bạch.</span>
              <span className="float-tag">
                <Leaf size={15} /> Thêm một lần tái sử dụng
              </span>
            </div>
          </div>
        </div>
        <small>Hệ thống chia sẻ và tái sử dụng tài sản nội bộ</small>
      </div>
      <div className="login-form">
        <div className="login-form-inner">
          <span className="section-kicker">CHÀO MỪNG TRỞ LẠI</span>
          <h2>Đăng nhập</h2>
          <p>Sử dụng tài khoản do tổ chức cấp.</p>
          <ActionForm
            onSubmit={async () => {
              await login(username, password);
              navigate("/", { replace: true });
            }}
            submitLabel="Đăng nhập"
          >
            <Field label="Tên đăng nhập">
              <input
                required
                autoComplete="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Nhập tên đăng nhập"
              />
            </Field>
            <Field label="Mật khẩu">
              <input
                required
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Nhập mật khẩu"
              />
            </Field>
          </ActionForm>
          <div className="login-security">
            <ShieldCheck size={18} /> Quyền truy cập được phân theo vai trò và
            đơn vị.
          </div>
        </div>
      </div>
    </div>
  );
}
function Layout() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [menu, setMenu] = useState(false),
    [account, setAccount] = useState(false),
    [changePassword, setChangePassword] = useState(false),
    [current, setCurrent] = useState(""),
    [next, setNext] = useState(""),
    [error, setError] = useState("");
  if (!user) return null;
  const member = user.roles.some((r) => ["THANH_VIEN", "QUAN_LY"].includes(r)),
    manager = user.roles.includes("QUAN_LY"),
    admin = user.roles.includes("QUAN_TRI");
  const businessNav = [
    { to: "/", text: "Tổng quan", icon: LayoutDashboard },
    ...(member
      ? [
          { to: "/assets", text: "Khám phá tài sản", icon: Search },
          { to: "/loans", text: "Phiếu mượn của tôi", icon: ClipboardList },
          { to: "/owned", text: "Tài sản đơn vị", icon: Boxes },
        ]
      : []),
    ...(manager
      ? [
          { to: "/review", text: "Xử lý mượn–trả", icon: ShieldCheck },
          {
            to: "/effectiveness",
            text: "Hiệu quả sử dụng",
            icon: ChartNoAxesCombined,
          },
        ]
      : []),
  ];
  const nav = admin
    ? [{ to: "/admin", text: "Quản trị hệ thống", icon: Settings }]
    : businessNav;
  const currentNav =
    nav.find((x) => x.to !== "/" && location.pathname.startsWith(x.to)) ||
    nav[0];
  return (
    <div className="app-shell">
      <div
        className={`sidebar-overlay ${menu ? "visible" : ""}`}
        onClick={() => setMenu(false)}
      />
      <aside className={`sidebar ${menu ? "opened" : ""}`}>
        <div className="sidebar-header">
          <Link className="brand" to={admin ? "/admin" : "/"}>
            <span className="brand-icon">
              <Leaf />
            </span>
            <div>
              <span className="brand-title">
                ENV<span>09</span>
              </span>
              <span className="sidebar-caption">Chia sẻ & Tái sử dụng</span>
            </div>
          </Link>
        </div>
        <div className="sidebar-body">
          <div className="nav-caption">KHÔNG GIAN LÀM VIỆC</div>
          <nav>
            {nav.map((n) => (
              <NavLink
                key={n.to}
                to={n.to}
                end={n.to === "/"}
                onClick={() => setMenu(false)}
              >
                <n.icon size={19} />
                <span>{n.text}</span>
              </NavLink>
            ))}
          </nav>
        </div>
        <div className="sidebar-bottom">
          <div className="unit-icon">
            <Boxes size={19} />
          </div>
          <div className="sidebar-unit-info">
            <strong>{user.unit_name}</strong>
            {user.unit_address && <small>{user.unit_address}</small>}
            <small>Một tổ chức, cùng chia sẻ.</small>
          </div>
        </div>
      </aside>
      <div className="workspace">
        <header className="topbar">
          <div className="topbar-left">
            <button
              aria-label="Mở menu"
              className="icon-button mobile-menu"
              onClick={() => setMenu(!menu)}
            >
              {menu ? <X /> : <Menu />}
            </button>
            <span>Không gian nội bộ</span>
            <span className="topbar-divider">/</span>
            <strong>{currentNav.text}</strong>
          </div>
          <div className="topbar-actions">
            {member && !admin && <NotificationBell />}
            <div className="account-wrap">
              <button
                className="account-button"
                onClick={() => setAccount(!account)}
              >
                <span className="avatar">
                  {user.name.split(" ").slice(-1)[0].slice(0, 1)}
                </span>
                <span>
                  <strong>{user.name}</strong>
                  <small>{user.roles.map(label).join(", ")}</small>
                </span>
                <ChevronDown size={16} />
              </button>
              {account && (
                <div className="account-menu">
                  <button
                    onClick={() => {
                      setAccount(false);
                      setChangePassword(true);
                    }}
                  >
                    Đổi mật khẩu
                  </button>
                  <button
                    onClick={async () => {
                      try {
                        await logout();
                      } catch (e) {
                        setError(String(e));
                      }
                    }}
                  >
                    <LogOut size={16} /> Đăng xuất
                  </button>
                </div>
              )}
            </div>
          </div>
        </header>
        <main className="main-content">
          <ErrorBox message={error} />
          <Outlet />
        </main>
        <footer className="footer">
          <span>ENV09 — Chia sẻ và tái sử dụng tài sản nội bộ</span>
          <span>
            Sử dụng hiệu quả. Giảm mua mới. <ArrowUpRight size={13} />
          </span>
        </footer>
      </div>
      {changePassword && (
        <Modal title="Đổi mật khẩu" onClose={() => setChangePassword(false)}>
          <ActionForm
            submitLabel="Đổi mật khẩu"
            onSubmit={async () => {
              await send("/auth/password", {
                current_password: current,
                new_password: next,
              });
              window.dispatchEvent(new Event("session-expired"));
            }}
          >
            <div className="form-grid">
              <Field label="Mật khẩu hiện tại" wide>
                <input
                  required
                  type="password"
                  autoComplete="current-password"
                  value={current}
                  onChange={(e) => setCurrent(e.target.value)}
                />
              </Field>
              <Field label="Mật khẩu mới (ít nhất 8 ký tự)" wide>
                <input
                  required
                  minLength={8}
                  type="password"
                  autoComplete="new-password"
                  value={next}
                  onChange={(e) => setNext(e.target.value)}
                />
              </Field>
            </div>
          </ActionForm>
        </Modal>
      )}
    </div>
  );
}
function Guard({
  role,
  children,
}: {
  role?: string;
  children: React.ReactNode;
}) {
  const { user } = useAuth();
  if (role && !user?.roles.includes(role)) return <Navigate to="/" replace />;
  return children;
}
function Root() {
  const { user, loading } = useAuth();
  if (loading) return <Loading />;
  if (!user) return <Login />;
  if (user.roles.includes("QUAN_TRI"))
    return (
      <Routes>
        <Route element={<Layout />}>
          <Route path="admin" element={<Admin />} />
          <Route path="*" element={<Navigate to="/admin" replace />} />
        </Route>
      </Routes>
    );
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="assets" element={<Assets />} />
        <Route path="assets/:id" element={<AssetDetail />} />
        <Route path="owned" element={<Assets own />} />
        <Route path="owned/:id" element={<AssetDetail />} />
        <Route path="loans" element={<Borrowing />} />
        <Route
          path="review"
          element={
            <Guard role="QUAN_LY">
              <Loans manage />
            </Guard>
          }
        />
        <Route path="loans/:id" element={<LoanDetail />} />
        <Route
          path="needs"
          element={<Navigate to="/loans?tab=needs" replace />}
        />
        <Route path="needs/:id" element={<NeedDetail />} />
        <Route
          path="verification"
          element={
            <Guard role="QUAN_LY">
              <Navigate to="/effectiveness" replace />
            </Guard>
          }
        />
        <Route
          path="indicator"
          element={
            <Guard role="QUAN_LY">
              <Navigate to="/effectiveness?tab=indicator" replace />
            </Guard>
          }
        />
        <Route
          path="effectiveness"
          element={
            <Guard role="QUAN_LY">
              <Effectiveness />
            </Guard>
          }
        />
        <Route
          path="admin"
          element={
            <Guard role="QUAN_TRI">
              <Admin />
            </Guard>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
export default function App() {
  return (
    <BrowserRouter>
      <ToastProvider>
        <AuthProvider>
          <Root />
        </AuthProvider>
      </ToastProvider>
    </BrowserRouter>
  );
}
