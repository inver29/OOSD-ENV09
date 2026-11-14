# ĐỒ ÁN CUỐI KỲ: HỆ THỐNG CHIA SẺ VÀ TÁI SỬ DỤNG TÀI SẢN NỘI BỘ (ENV09)

- **Họ và tên:** Nguyễn Hoài An
- **Lớp:** 12_ĐH_CNPM1
- **MSSV:** 1250080245
- **Trường:** Đại học Tài nguyên và Môi trường TP.HCM
- **Môn học:** Phương pháp phát triển phần mềm hướng đối tượng
- **Giảng viên hướng dẫn:** ThS. Phạm Trọng Huynh

## 1. Môi trường phát triển

- Nền tảng: website dùng React và TypeScript cho giao diện, Python và FastAPI cho API.
- Cơ sở dữ liệu: Microsoft SQL Server 2022, kết nối qua SQLAlchemy và ODBC Driver 17 hoặc 18.
- Môi trường chạy: Python 3.12 trở lên, Node.js 22 và PowerShell trên Windows.
- Công cụ mô hình hóa và kiểm thử: draw.io, pytest và Playwright.

## 2. Nội dung đã thực hiện

- Phân tích nghiệp vụ mượn tài sản giữa các đơn vị cùng tổ chức với ba vai trò: thành viên, quản lý tài sản và quản trị hệ thống. Mỗi tài khoản có một vai trò.
- Dựng sơ đồ use case, lớp, trạng thái, tuần tự, hoạt động, ERD, kiến trúc và thiết kế giao diện. Tệp draw.io và ảnh tương ứng nằm trong [Sơ đồ](S%C6%A1%20%C4%91%E1%BB%93/).
- Thiết kế 13 bảng và các ràng buộc khóa, thời gian, trạng thái trong SQL Server. Tập lệnh cài mới nằm trong [ENV09.sql](ENV09.sql) và [Web/sql/001_schema.sql](Web/sql/001_schema.sql). Các tập lệnh nâng cấp nằm trong [Web/sql](Web/sql/).
- Xây dựng frontend trong [Web/frontend](Web/frontend/) và backend trong [Web/backend](Web/backend/). Các thao tác xét duyệt, giao nhận và thu hồi kiểm tra quyền, trạng thái và dữ liệu liên quan trước khi lưu.

## 3. Kết quả đạt được

- **Thành viên:** đăng ký và theo dõi hồ sơ tài sản mình phụ trách, tra cứu hiện vật của đơn vị khác, gửi hoặc hủy phiếu mượn, xác nhận nhận và trả tài sản. Sau khi hoàn trả, người lập có thể khai báo kết quả mua mới.
- **Quản lý tài sản:** xét duyệt hồ sơ tài sản và phiếu mượn của đơn vị mình phụ trách, lập biên bản giao nhận, xử lý sự cố, đánh giá vòng đời và xác minh nhu cầu thuộc đơn vị mình. Khi quản lý mượn tài sản của đơn vị khác, quản lý đơn vị sở hữu xét duyệt.
- **Quản trị hệ thống:** quản lý tài khoản, đơn vị, địa điểm, loại tài sản và chính sách mượn. Sau khi đăng nhập, quản trị đi thẳng vào trang Quản trị hệ thống.
- **Chỉ số tránh mua mới:** đối chiếu phương án ban đầu và kết quả xác minh sau hoàn trả. Chỉ số tính tỷ lệ nhu cầu tránh mua mới trong các nhu cầu đã xác minh có dự định mua, theo kỳ và đơn vị được chọn.
- Đợt kiểm chứng ngày 14/11/2026 ghi nhận 65/65 ca backend và 14/14 kịch bản trình duyệt đạt trên SQL Server thử. [Kết quả kiểm thử](Web/docs/KIEM_THU.md)

## 4. Lỗi gặp phải

- Hai yêu cầu xét duyệt đồng thời có thể tranh cùng một tài sản. Backend khóa bản ghi tài sản và kiểm tra lại trạng thái trong giao dịch trước khi duyệt.
- Sau khi sửa biên bản, một bên có thể vẫn mở phiên bản cũ. Hệ thống yêu cầu hai bên xác nhận cùng phiên bản trước khi hoàn tất giao nhận.
- Khi thu hồi có thể còn phiếu chưa giao hoặc tài sản đang được mượn. Hệ thống lưu thông báo trước khi xóa phiếu chưa giao. Với phiếu đã giao, tài sản chuyển sang Chờ thu hồi và hồ sơ ẩn sau khi hoàn tất nhận trả.

## 5. Hướng dẫn chạy chương trình

### Bước 1. Cấu hình kết nối SQL Server

Mở CMD trong thư mục gốc của repository. Tạo tệp cấu hình cục bộ nếu máy chưa có:

```cmd
cd /d Web
if not exist .env copy .env.example .env
notepad .env
```

Sửa APP_DB_SERVER và APP_DB_DRIVER theo SQL Server và driver trên máy. Với xác thực Windows, đặt APP_DB_TRUSTED=true. Đặt APP_DEMO_PASSWORD ít nhất 8 ký tự trước khi nạp dữ liệu mẫu.

### Bước 2. Khởi tạo cơ sở dữ liệu và cài chương trình

Chạy từ thư mục Web:

```cmd
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r backend\requirements-dev.txt
.venv\Scripts\python.exe -m backend.app.bootstrap --seed
cd frontend
npm ci
npm run build
cd ..
```

Lệnh bootstrap tạo cấu trúc và nạp dữ liệu mẫu khi chưa có tài khoản. Xem tập lệnh tạo bảng tại [ENV09.sql](ENV09.sql).

### Bước 3. Khởi chạy và thử nghiệp vụ

```cmd
.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Mở [website ENV09](http://127.0.0.1:8000). Dùng mật khẩu demo đã cấu hình và các tài khoản mẫu `an`, `ql.hcm` hoặc `admin` để xem theo từng vai trò. Để thử luồng mượn giữa hai đơn vị, đăng nhập bằng thành viên, chọn hiện vật của đơn vị khác, gửi phiếu rồi dùng tài khoản quản lý của đơn vị sở hữu để xét duyệt. Mở hai hồ sơ trình duyệt riêng để giữ hai phiên đăng nhập khi thử giao nhận.

Xem thêm [hướng dẫn cài đặt và vận hành](Web/README.md) và [luồng chức năng](Web/docs/LUONG_CHUC_NANG.md).

## Ảnh giao diện minh họa

[Tổng quan](Web/docs/anh/dashboard-desktop.png) · [Khám phá tài sản](Web/docs/anh/catalog-desktop.png) · [Xét duyệt yêu cầu](Web/docs/anh/approval-popup.png) · [Hoàn trả](Web/docs/anh/loan-return-desktop.png) · [Chỉ số tránh mua mới](Web/docs/anh/effectiveness-desktop.png) · [Quản trị](Web/docs/anh/admin-filters-live-desktop.png)
