export const labels: Record<string, string> = {
  THANH_VIEN: "Thành viên",
  QUAN_LY: "Quản lý tài sản",
  QUAN_TRI: "Quản trị",
  NHAP: "Bản nháp",
  CHO_CHIA_SE: "Đang chia sẻ",
  CHO_BAN_GIAO: "Chờ bàn giao",
  DA_DUOC_MUON: "Đã được mượn",
  BAO_TRI: "Bảo trì",
  CHO_THU_HOI: "Chờ thu hồi",
  DA_THU_HOI: "Đã thu hồi",
  THU_HOI: "Thu hồi tài sản",
  CHO_DUYET: "Chờ duyệt",
  DA_DUYET: "Chờ bàn giao",
  TU_CHOI: "Từ chối",
  DA_HUY: "Đã hủy",
  HET_HAN_NHAN: "Hết hạn nhận",
  DANG_MUON: "Đang mượn",
  CHO_XAC_NHAN_TRA: "Chờ xác nhận trả",
  DA_DONG: "Đã hoàn trả",
  CHO_XAC_MINH: "Chờ xác minh",
  DA_XAC_MINH: "Đã xác minh",
  CHO_XAC_NHAN: "Chờ xác nhận",
  HOAN_TAT: "Hoàn tất",
  MUA_MOI: "Mua mới",
  THUE_NGOAI: "Thuê ngoài",
  DUNG_TAI_SAN_KHAC: "Dùng tài sản khác",
  HOAN_NHU_CAU: "Hoãn nhu cầu sử dụng",
  CAP_NHAT: "Cập nhật",
  SU_CO: "Sự cố",
  XU_LY: "Xử lý",
  DANH_GIA: "Đánh giá",
  TIEP_TUC: "Tiếp tục chia sẻ",
  GIAO: "Bàn giao",
  TRA: "Hoàn trả",
  OVERDUE: "Quá hạn trả",
};
export const label = (s: string) => labels[s] || s;
export const needAlternatives = ["MUA_MOI", "HOAN_NHU_CAU"];
export function date(
  value: string | null | undefined,
  time = true,
  timeZone?: string,
) {
  return value
    ? new Intl.DateTimeFormat("vi-VN", {
        timeZone,
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        ...(time ? { hour: "2-digit", minute: "2-digit" } : {}),
      }).format(new Date(value))
    : "—";
}
export function localDate(value?: string | Date) {
  const d = value ? new Date(value) : new Date();
  return new Date(d.getTime() - d.getTimezoneOffset() * 60000)
    .toISOString()
    .slice(0, 16);
}
export const iso = (s: string) => new Date(s).toISOString();
export const errorText = (e: unknown) =>
  e instanceof Error ? e.message : "Có lỗi xảy ra. Vui lòng thử lại.";
export const openStates = [
  "CHO_DUYET",
  "DA_DUYET",
  "DANG_MUON",
  "CHO_XAC_NHAN_TRA",
];
export const loanStageStates = [...openStates, "DA_DONG"];
export const loanStates = [
  ...loanStageStates,
  "TU_CHOI",
  "DA_HUY",
  "HET_HAN_NHAN",
  "OVERDUE",
];
export const handoverLabels: Record<string, string> = {
  NHAP: "Chưa xác nhận",
  CHO_XAC_NHAN: "Chờ xác nhận",
  HOAN_TAT: "Hoàn tất",
  DA_HUY: "Đã hủy",
};
