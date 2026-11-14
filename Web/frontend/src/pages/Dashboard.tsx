import { Link } from "react-router-dom";
import {
  ArrowRight,
  ArrowUpRight,
  Boxes,
  CheckCheck,
  Clock3,
  Leaf,
  MoveUpRight,
  ShieldCheck,
} from "lucide-react";
import { useAuth } from "../context";
import { useData } from "../hooks";
import type { DashboardData } from "../types";
import { Empty, ErrorBox, Loading, PageHeader } from "../components/ui";
import LoanTable from "../components/LoanTable";
export default function Dashboard() {
  const { user, lookups } = useAuth();
  const { data, loading, error } = useData<DashboardData>("/dashboard");
  if (!user) return null;
  const manager = user.roles.includes("QUAN_LY"),
    member = user.roles.some((r) => ["THANH_VIEN", "QUAN_LY"].includes(r));
  const stats = manager
    ? [
        {
          title: "Yêu cầu chờ duyệt",
          value: data?.pending,
          to: "/review",
          icon: ShieldCheck,
        },
        {
          title: "Phiếu đang quá hạn",
          value: data?.overdue,
          to: "/review?status=OVERDUE",
          icon: Clock3,
        },
        {
          title: "Nhu cầu chờ xác minh",
          value: data?.need_review,
          to: "/effectiveness",
          icon: CheckCheck,
        },
        {
          title: "Tài sản cần xử lý",
          value: data?.paused,
          to: "/owned",
          icon: Boxes,
        },
      ]
    : member
      ? [
          {
            title: "Tài sản đang chia sẻ",
            value: data?.shared,
            to: "/assets",
            icon: Boxes,
          },
          {
            title: "Phiếu đang mở",
            value: data?.my_open,
            to: "/loans",
            icon: MoveUpRight,
          },
          {
            title: "Tài sản đang mượn",
            value: data?.my_holding,
            to: "/loans?status=DANG_MUON",
            icon: CheckCheck,
          },
          {
            title: "Phiếu quá hạn trả",
            value: data?.my_overdue,
            to: "/loans?status=OVERDUE",
            icon: Clock3,
          },
        ]
      : [
          {
            title: "Tài khoản",
            value: data?.users,
            to: "/admin",
            icon: ShieldCheck,
          },
          { title: "Đơn vị", value: data?.units, to: "/admin", icon: Boxes },
          {
            title: "Tài sản toàn tổ chức",
            value: data?.assets,
            to: "/admin",
            icon: Leaf,
          },
        ];
  return (
    <>
      <PageHeader
        eyebrow="TỔNG QUAN"
        title={`Chào ${user.name.split(/\s*[-–—]\s*/)[0]},`}
        description="Mỗi lần chia sẻ là thêm một lần sử dụng hiệu quả."
        action={
          member && (
            <Link className="btn primary" to="/assets">
              Khám phá tài sản <ArrowUpRight size={17} />
            </Link>
          )
        }
      />
      <ErrorBox message={error} />
      <section className="dashboard-hero">
        <div>
          <span className="hero-label">
            <span /> KẾT NỐI NGUỒN LỰC NỘI BỘ
          </span>
          <h2>
            Có sẵn ở nơi khác.
            <br />
            Hữu ích tại đơn vị bạn.
          </h2>
          <p>Tra cứu thiết bị, chọn lịch phù hợp và gửi yêu cầu mượn.</p>
          {member && (
            <Link to="/assets" className="hero-link">
              Tìm tài sản phù hợp <ArrowRight size={18} />
            </Link>
          )}
        </div>
        <div className="hero-art" aria-hidden="true">
          <div className="hero-circle" />
          <Boxes size={146} strokeWidth={0.9} />
          <div className="hero-leaf">
            <Leaf size={28} />
          </div>
          <span>CHIA SẺ ĐỂ TIẾP NỐI</span>
        </div>
      </section>
      <div className="stats-grid">
        {stats.map((s) => (
          <Link to={s.to} className="stat-card" key={s.title}>
            <div>
              <span className="stat-icon">
                <s.icon size={20} />
              </span>
              <ArrowUpRight size={17} />
            </div>
            <strong>{s.value ?? "—"}</strong>
            <span>{s.title}</span>
          </Link>
        ))}
      </div>
      <div className="dashboard-lower">
        <section className="panel">
          <div className="panel-heading">
            <div>
              <h2>Phiếu mượn gần đây</h2>
              <p>Cập nhật từ các luồng đang xử lý.</p>
            </div>
            {member && (
              <Link className="text-link" to={manager ? "/review" : "/loans"}>
                Xem tất cả <ArrowRight size={16} />
              </Link>
            )}
          </div>
          {loading && !data ? (
            <Loading />
          ) : data?.recent.length ? (
            <LoanTable loans={data.recent} manage={manager} />
          ) : (
            <Empty text="Chưa có phiếu mượn." />
          )}
        </section>
        <aside className="panel policy-card">
          <div className="round-icon">
            <ShieldCheck />
          </div>
          <h2>Chính sách đang áp dụng</h2>
          {lookups?.policy ? (
            <>
              <p>{lookups.policy.name}</p>
              <dl>
                <div>
                  <dt>Mượn tối đa</dt>
                  <dd>{lookups.policy.max_days} ngày</dd>
                </div>
                <div>
                  <dt>Thời gian nhận</dt>
                  <dd>{lookups.policy.pickup_hours} giờ</dd>
                </div>
                <div>
                  <dt>Dự phòng sau trả</dt>
                  <dd>{lookups.policy.buffer_hours} giờ</dd>
                </div>
              </dl>
              <small>
                Thời hạn và chính sách cụ thể được lưu theo từng phiếu mượn.
              </small>
            </>
          ) : (
            <p>Chưa có chính sách có hiệu lực.</p>
          )}
        </aside>
      </div>
    </>
  );
}
