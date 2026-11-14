import { useData } from "../hooks";
import type { Asset, Loan } from "../types";
import { date } from "../utils";
import { Badge, DataItem, DeviceArt, ErrorBox, Loading, Modal } from "./ui";
import DecisionActions from "./DecisionActions";

export default function QuickReview({
  asset,
  loan,
  onClose,
  onDone,
}: {
  asset?: Asset;
  loan?: Loan;
  onClose: () => void;
  onDone: () => void;
}) {
  const {
    data: calendar,
    loading,
    error,
  } = useData<Asset>(loan ? `/assets/${loan.asset_id}` : null);
  const finish = () => {
    onDone();
    onClose();
  };
  return (
    <Modal
      title={asset ? "Duyệt đăng ký tài sản" : "Xét duyệt yêu cầu mượn"}
      onClose={onClose}
    >
      {asset ? (
        <>
          <div className="selected-asset">
            <DeviceArt
              category={asset.category_name}
              name={asset.name}
              image={asset.image_path}
            />
            <div>
              <strong>{asset.name}</strong>
              <p>{asset.custodian_name}</p>
            </div>
          </div>
          <div className="data-grid">
            <DataItem title="Loại tài sản">{asset.category_name}</DataItem>
            <DataItem title="Địa điểm">{asset.location_name}</DataItem>
            <DataItem title="Tình trạng">{asset.condition}</DataItem>
            <DataItem title="Đặc tính / Phụ kiện">{asset.description}</DataItem>
          </div>
          <DecisionActions
            embedded
            onCancel={onClose}
            path={`/assets/${asset.id}/review`}
            version={asset.version}
            onDone={finish}
          />
        </>
      ) : (
        loan && (
          <>
            <h2>{loan.asset_name}</h2>
            <div className="data-grid">
              <DataItem title="Người mượn">{loan.borrower_name}</DataItem>
              <DataItem title="Đơn vị">{loan.borrower_unit_name}</DataItem>
              <DataItem title="Nhận từ">{date(loan.start_at)}</DataItem>
              <DataItem title="Trả trước">{date(loan.end_at)}</DataItem>
            </div>
            <p className="pre-line">{loan.purpose}</p>
            <h2>Lịch đã giữ</h2>
            <ErrorBox message={error} />
            {loading && !calendar ? (
              <Loading />
            ) : calendar?.calendar?.length ? (
              calendar.calendar.map((r, i) => (
                <div className="calendar-slot" key={i}>
                  <Badge status={r.status} overdue={r.overdue} />
                  <span>
                    {date(r.start_at)} → {date(r.end_at)}
                  </span>
                </div>
              ))
            ) : (
              <p className="muted">Chưa có lịch giữ chỗ.</p>
            )}
            <DecisionActions
              embedded
              onCancel={onClose}
              path={`/loans/${loan.id}/decision`}
              onDone={finish}
            />
          </>
        )
      )}
    </Modal>
  );
}
