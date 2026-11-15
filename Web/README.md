# ENV09 — Chia sẻ và tái sử dụng tài sản nội bộ

Website cho một tổ chức có nhiều đơn vị/chi nhánh. Thành viên tra cứu và mượn hiện vật từ đơn vị khác; quản lý của đơn vị sở hữu xét duyệt, bàn giao, nhận trả và đánh giá vòng đời. Hệ thống tính chỉ số tránh mua mới từ nhu cầu đã được khai báo và xác minh.

**Công nghệ:** React + TypeScript, FastAPI, SQLAlchemy, SQL Server. Có cấu hình Docker và OpenTelemetry tùy chọn. Frontend và API được phục vụ chung một địa chỉ; phông chữ được đóng gói tại máy, không cần Google Fonts.

## 1. Chạy tại máy hiện tại

Đã cấu hình kết nối Windows tương tự các lab:

```ini
APP_DB_SERVER=.\MSSQLSERVER08
APP_DB_NAME=ENV09
APP_DB_DRIVER=ODBC Driver 17 for SQL Server
APP_DB_TRUSTED=true
```

Mở START.bat hoặc dùng CMD tại thư mục Web:

```cmd
.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

- Website: **http://127.0.0.1:8000**
- API: http://127.0.0.1:8000/api/docs
- Kiểm tra kết nối: http://127.0.0.1:8000/api/health
- Dừng máy chủ: `Ctrl+C` tại cửa sổ đang chạy.

Nếu cổng 8000 đang được sử dụng, dùng `scripts\run.ps1 -Port 8010`. Sau khi sửa frontend, chạy `scripts\run.ps1 -Build` để dựng lại bản dùng chung với backend.

### Tài khoản dữ liệu mẫu

Thành viên và quản lý vào **Tổng quan** sau đăng nhập. Quản trị vào thẳng **Quản trị hệ thống**, chỉ có điều hướng quản trị.

Các tài khoản mẫu dùng mật khẩu do người cài đặt đặt trong biến APP_DEMO_PASSWORD ở tệp cấu hình cục bộ. Có thể đổi mật khẩu trong menu tài khoản.

| Tên đăng nhập | Vai trò | Đơn vị |
|---|---|---|
| `an` | Thành viên | TP. Hồ Chí Minh |
| `binh` | Thành viên | Đà Nẵng |
| `chi` | Thành viên | Hà Nội |
| `ql.hn` | Quản lý tài sản | Hà Nội |
| `ql.hcm` | Quản lý tài sản | TP. Hồ Chí Minh |
| `ql.dn` | Quản lý tài sản | Đà Nẵng |
| `admin` | Quản trị hệ thống | Hà Nội |

Dùng hai cửa sổ trình duyệt với hồ sơ khác nhau hoặc cửa sổ riêng tư để thử hai bên giao nhận. Các tab trong cùng hồ sơ dùng chung phiên đăng nhập.

## 2. Cài mới

Cần Python 3.12 trở lên, Node.js 22, SQL Server 2022 và ODBC Driver 17 hoặc 18. Mở CMD tại thư mục gốc repository:

```cmd
cd /d Web
if not exist .env copy .env.example .env
notepad .env
```

Chỉnh APP_DB_SERVER và APP_DB_DRIVER theo môi trường. Chọn kiểu xác thực phù hợp. Đặt APP_DEMO_PASSWORD ít nhất 8 ký tự trước khi nạp dữ liệu mẫu.

```cmd
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r backend\requirements-dev.txt
.venv\Scripts\python.exe -m backend.app.bootstrap --seed
cd frontend
npm ci
npm run build
cd ..
```

Lệnh bootstrap kiểm tra cấu trúc, tạo database nếu cần và nạp demo khi chưa có người dùng. Để bắt đầu với database trống, bỏ --seed, giữ APP_SEED_DEMO=false và tạo quản trị qua lệnh sau:

```cmd
.venv\Scripts\python.exe -m backend.app.create_admin
```

Mật khẩu nhập ẩn. Sau khi đăng nhập, quản trị tạo đơn vị, địa điểm, loại tài sản, chính sách và tài khoản. Mỗi tài khoản được cấp đúng một vai trò.

### Phát triển có tự tải lại

Hai terminal tại thư mục `Web`:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

```powershell
cd frontend
npm.cmd run dev
```

Truy cập http://127.0.0.1:5173. Vite chuyển `/api` sang FastAPI; không lưu token trong localStorage.

## 3. Chức năng theo tác nhân

| Tác nhân | Thao tác |
|---|---|
| Thành viên | Đăng nhập/đổi mật khẩu; tra cứu, lọc tài sản và lịch trống; xem hồ sơ; thêm tài sản chờ quản lý chi nhánh duyệt và thu hồi tài sản mình phụ trách; gửi/hủy phiếu; xác nhận giao nhận; báo trả, báo sự cố; khai báo kết quả mua mới sau hoàn trả. |
| Quản lý tài sản | Các thao tác thành viên; duyệt/từ chối đăng ký tài sản trong đơn vị; chỉ sửa/thu hồi hồ sơ mình phụ trách; duyệt/từ chối phiếu mượn; lập, sửa, hủy/mở lại biên bản; xác nhận giao nhận; xử lý sự cố và quyết định vòng đời; xác minh nhu cầu của đơn vị; xem chỉ số và xuất CSV. |
| Quản trị | Quản lý tài khoản và vai trò, đơn vị, địa điểm, loại tài sản, chính sách mượn. Xóa danh mục/chính sách chỉ khi chưa được tham chiếu. |

### Điều hướng gọn theo vai trò

- Thành viên: **Tổng quan**, **Khám phá tài sản**, **Phiếu mượn của tôi**, **Tài sản đơn vị**. Nhu cầu sử dụng nằm trong tab của trang phiếu mượn.
- Quản lý: có thêm **Xử lý mượn–trả** (lọc theo tiến độ) và **Hiệu quả sử dụng** (hai tab xác minh nhu cầu và chỉ số).
- Quản trị: chỉ có **Quản trị hệ thống**.

### Luồng sử dụng

Phiếu mượn dùng thống nhất: **Chờ duyệt → Chờ bàn giao → Đang mượn → Chờ xác nhận trả → Đã hoàn trả**. Quá hạn trả là nhãn cảnh báo đi kèm bước hiện tại.

Tìm kiếm tự cập nhật sau khoảng 300 ms khi nhập; dropdown áp dụng ngay. Lọc lịch trống và bộ lọc chỉ số tự tải khi đã nhập đủ khoảng thời gian hợp lệ, không có nút Tìm/Xem kết quả.

1. Thành viên **Thêm** tài sản → Chờ duyệt. Quản lý thêm tài sản → tự duyệt thành Đang chia sẻ. Người thêm luôn là người phụ trách, không chuyển cho tài khoản khác. Quản lý xem và duyệt/từ chối ngay từ danh sách tài sản đơn vị. Chỉ người phụ trách được sửa/thu hồi, kể cả khi người đang xem là quản lý. Thu hồi xóa các phiếu còn chờ duyệt/chờ bàn giao và ẩn tài sản; nếu còn người mượn thì chuyển Chờ thu hồi, tự ẩn sau khi hai bên hoàn tất nhận trả.
2. Thành viên đơn vị khác xem thông tin/lịch → Đặt mượn tài sản → nhập thời gian, mục đích và phương án **Mua mới/Hoãn nhu cầu sử dụng** nếu không mượn được → Gửi yêu cầu. Hệ thống tự tạo nhu cầu Chờ xác minh cùng phiếu, không có bước chọn liên kết nhu cầu hoặc đính kèm dự định mua. Không thêm nhu cầu riêng; nhu cầu tự hiện trong danh sách sau khi hoàn trả hoàn tất.
3. Quản lý chọn **Xét duyệt** ở dòng phiếu → đối chiếu thông tin/lịch trong popup → **Duyệt**, hoặc nhập lý do **Từ chối**. Ở trang chi tiết, Duyệt/Từ chối mở popup để xác nhận trước khi ghi. Duyệt phiếu → tài sản **Chờ bàn giao**, ẩn khỏi Khám phá; tất cả phiếu còn chờ của tài sản đó tự Từ chối với lý do **Đã có người khác mượn tài sản này**. Mỗi tài sản chỉ có một phiếu đã duyệt/đang mượn. Hủy hoặc hết hạn nhận mở lại tài sản nếu vẫn đủ điều kiện chia sẻ; phiếu đã từ chối được giữ nguyên.
4. Khi giao, quản lý nhập nội dung và bấm **Xác nhận bàn giao** một lần; người mượn đọc và bấm **Đã nhận tài sản**. Đủ hai bên → phiếu Đang mượn, tài sản **Đã được mượn** và tiếp tục ẩn khỏi Khám phá.
5. Khi trả, người mượn nhập tình trạng/nội dung và bấm **Xác nhận trả tài sản**; quản lý kiểm tra rồi bấm **Xác nhận đã nhận trả**. Đủ hai bên mới đóng phiếu. Nếu sửa nội dung, bên còn lại phải xác nhận phiên bản mới. Trả hỏng tự chuyển Bảo trì; tài sản Chờ thu hồi tự ẩn sau nhận trả.
6. Khi không còn người giữ và không Chờ thu hồi, quản lý ghi kết quả xử lý, tình trạng và quyết định Tiếp tục chia sẻ/Bảo trì trong một form **Xử lý & đánh giá vòng đời**. Không cần lập riêng một bước xử lý rồi một bước đánh giá.
7. Sau hoàn trả, người lập khai báo kết quả mua ngay trên phiếu liên kết hoặc hồ sơ nhu cầu. Quản lý đơn vị có nhu cầu vào **Hiệu quả sử dụng** để xác minh và xem chỉ số.

## 4. Quy tắc quan trọng

- Một phiếu mượn một hiện vật; người mượn thuộc đơn vị khác đơn vị sở hữu. Mọi quyền nghiệp vụ đều kiểm tra ở backend.
- Không tự duyệt phiếu, tự xác minh nhu cầu hoặc xác nhận thay cả hai bên.
- Giữ lịch theo khoảng `[bắt đầu, kết thúc + giờ dự phòng)`. Sau khi đóng phiếu, dùng thời điểm trả thực tế cộng giờ dự phòng. Quá hạn trả vẫn giữ trách nhiệm và chặn duyệt thêm, không tự đóng phiếu.
- Ghi lịch và đổi trạng thái nằm trong cùng giao dịch SQL. Các thao tác mượn/giao nhận khóa theo thứ tự **tài sản → phiếu → biên bản**, kiểm tra lại trước khi ghi.
- Sửa/mở lại biên bản tăng phiên bản và xóa hai xác nhận cũ; thao tác Lưu & xác nhận ghi ngay xác nhận của người đang sửa. Lưu lại đúng nội dung/phiên bản hiện tại không tăng phiên bản hoặc xóa xác nhận bên kia. Biên bản hoàn tất giữ nguyên. Xác nhận phiên bản cũ bị từ chối.
- Hủy trước giao hoặc hết hạn nhận giải phóng lịch. Tác vụ máy chủ kiểm tra hết hạn mỗi 30 giây; kiểm tra giờ nhận vẫn thực hiện trực tiếp khi bàn giao.
- Khi đánh giá tài sản hoặc mở lại sau xử lý, cần giải quyết các phiếu chưa giao bị ảnh hưởng. Không cho xử lý/đánh giá vòng đời khi còn người giữ. Bỏ Tạm ngừng và Ngừng sử dụng; dùng Bảo trì cho sửa chữa và Thu hồi tài sản để kết thúc chia sẻ.
- Hồ sơ tài sản dùng `ROWVERSION` để phát hiện chỉnh sửa đồng thời; mã yêu cầu UUID tránh tạo hai phiếu khi gửi lại cùng nội dung.
- Mật khẩu băm Argon2; cookie HttpOnly/SameSite; yêu cầu ghi có CSRF token; tệp ảnh/PDF tối đa 8 MB được kiểm tra và truy cập theo quyền.

### Chỉ số tránh mua mới

**D:** Số nhu cầu khác nhau có lượt mượn đã hoàn trả, đã xác minh có dự định mua và kết thúc dự kiến trong kỳ `[từ ngày, đến trước ngày)` của đơn vị đang xem.

**A:** Các nhu cầu trong D có phiếu đã đóng, việc mượn đáp ứng mục đích và người lập xác nhận không mua mới.

Chỉ số chỉ đánh giá các lượt đã mượn–trả, không đại diện cho toàn bộ nhu cầu của công ty.

**R = A / D × 100%**; D = 0 thì không tính tỷ lệ. Một nhu cầu tương ứng một hiện vật có thể phải mua; phương án mua được khai báo trước kết quả mượn và được quản lý khác người lập xác minh. Không dùng trọng số và không quy đổi thành tiền. Thay đổi kết quả mua sau xác minh sẽ đưa nhu cầu về chờ xác minh lại.

## 5. Dữ liệu và cấu trúc mã

Script cài mới `sql/001_schema.sql` có 13 bảng, 106 cột và 24 khóa ngoại. Bản `ENV09.sql` ở thư mục đồ án dùng cùng nội dung. Bảng `ThongBaoThuHoi` lưu mã người nhận, mã phiếu tại lúc thu hồi, tên tài sản, lý do và thời điểm đọc. Mã phiếu được lưu để tra cứu sau khi phiếu chưa bàn giao đã bị xóa. Để nâng cấp dữ liệu cũ, chạy `python -m backend.app.bootstrap` với cấu hình của dự án. Các script 002–009 áp dụng thay đổi theo phiên bản và giữ hồ sơ đã bàn giao.

| Nhóm | Bảng |
|---|---|
| Tổ chức, quyền | `DonVi`, `NguoiDung`, `PhanQuyen` |
| Tài sản | `LoaiTaiSan`, `DiaDiem`, `TaiSan`, `SuKienVongDoi` |
| Mượn và giao nhận | `ChinhSachMuon`, `PhieuMuon`, `BienBanGiaoNhan` |
| Đánh giá tránh mua mới | `NhuCauMuaMoi`, `XacMinhNhuCau` |

```text
Web/
├── backend/app/
│   ├── api/           # Nhận yêu cầu HTTP, kiểm tra phạm vi, trả DTO
│   ├── services/      # Nghiệp vụ và giao dịch
│   ├── models.py      # Ánh xạ đúng tên cột SQL của báo cáo
│   ├── schemas.py     # Dữ liệu đầu vào
│   ├── security.py    # Mật khẩu, phiên và CSRF
│   ├── bootstrap.py   # Khởi tạo từ SQL có sẵn
│   ├── seed.py        # Dữ liệu minh họa, không ghi đè
│   └── main.py        # Khởi động API, tác vụ hết hạn, phục vụ React
├── backend/tests/     # Kiểm thử nghiệp vụ trên SQL Server riêng
├── frontend/src/
│   ├── pages/        # Mỗi trang một file
│   ├── components/   # Biểu mẫu và thành phần dùng chung
│   ├── api.ts        # Fetch, lỗi và CSRF
│   └── styles.css    # Giao diện và bố cục điện thoại
├── frontend/tests/   # Kiểm thử thao tác trình duyệt
├── scripts/          # Khởi chạy ứng dụng trên Windows
└── sql/              # SQL Server và các migration
```

Ảnh vừa chọn được xem trước ngay trong form; nút Xem ảnh/Xem chứng từ mở popup tại trang hiện tại. PDF được hiển thị trong khung cùng nguồn.

Với cơ sở dữ liệu từ bản cũ, chạy lệnh `.venv\Scripts\python.exe -m backend.app.bootstrap` trong `Web` trước khi khởi động. Migration 009 đổi mã phiếu mượn hiện có và giữ lịch sử.

Trạng thái Chờ bàn giao/Đã được mượn được xác định từ phiếu hiện hành; `TaiSan.TrangThai` giữ trạng thái vòng đời. Khi hủy/đóng phiếu, nhãn hiển thị và danh sách tự đồng bộ, không cần thêm bảng/cột/FK.

Tệp đính kèm lưu tại `backend/storage/uploads`, không công khai thành thư mục tĩnh. Sao lưu thư mục này cùng database để giữ ảnh hiện trạng và chứng từ giao nhận. File Word và sơ đồ gốc không bị thay đổi bởi ứng dụng.

## 6. Kiểm thử

Kiểm thử backend tự tạo và dọn cơ sở dữ liệu riêng. Chạy trong CMD tại thư mục Web:

```cmd
.venv\Scripts\python.exe -m pytest backend/tests
.venv\Scripts\ruff.exe check backend
```

Kiểm thử giao diện dùng Edge và ghi dữ liệu. Chọn một tên database mới chỉ dùng cho kiểm thử, nhập mật khẩu demo cục bộ và khởi chạy bản thử:

```cmd
set "APP_DB_NAME=ENV09_Test_UI"
set "APP_STORAGE_DIR=%TEMP%\ENV09_Test_UI\uploads"
set /p "APP_DEMO_PASSWORD=Mat khau demo cho database thu: "
.venv\Scripts\python.exe -m backend.app.bootstrap --seed
.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8001
```

Mở CMD thứ hai tại Web. Nhập cùng mật khẩu đã dùng ở trên:

```cmd
set "UI_BASE_URL=http://127.0.0.1:8001"
set /p "DEMO_PASSWORD=Mat khau demo cho database thu: "
cd frontend
npm run test:ui
```

Khi kiểm thử xong, dừng máy chủ thử và có thể xóa database thử vừa tạo trong SSMS. Dùng database thử mới nếu muốn chạy lại với tập dữ liệu mẫu ban đầu. Xem [ca kiểm thử và kết quả](docs/KIEM_THU.md).

## 7. Docker và quan sát hệ thống

Docker chạy SQL Server riêng trong volume, không dùng Windows Integrated Security của máy chủ. Cấu hình này đã chuẩn bị; **chưa chạy container trên máy hiện tại vì chưa có Docker**.

```powershell
Copy-Item .env.docker.example .env.docker
# Sửa MSSQL_SA_PASSWORD và APP_DEMO_PASSWORD trước khi chạy.
docker compose --env-file .env.docker up --build -d
```

SQL Server Developer dùng cho học tập/phát triển. Dữ liệu nằm trong volume `sql_data`, tệp trong `uploads`. Không chạy lệnh xóa volume nếu cần giữ dữ liệu.

Mỗi yêu cầu có mã `X-Request-ID`, trạng thái và thời gian trong log. Để gửi trace OpenTelemetry, đặt `APP_OTEL_ENDPOINT` thành endpoint HTTP `/v1/traces` của collector rồi khởi động lại; để trống thì ứng dụng vẫn hoạt động bình thường.

Phiên đăng nhập đang lưu trong bộ nhớ một tiến trình để giữ cấu trúc gọn: dùng **một worker**; khởi động lại máy chủ sẽ yêu cầu đăng nhập lại. Khi triển khai cho nhiều người qua mạng, đặt sau HTTPS, bật `APP_COOKIE_SECURE=true` và cấu hình tài khoản SQL có quyền phù hợp. Chưa triển khai lên máy chủ công khai trong phạm vi lần làm này.

## 8. Tài liệu kỹ thuật tham khảo

- [FastAPI — Security](https://fastapi.tiangolo.com/tutorial/security/)
- [SQLAlchemy — SQL Server và pyodbc](https://docs.sqlalchemy.org/en/20/dialects/mssql.html#connecting-to-pyodbc)
- [Vite — Hướng dẫn](https://vite.dev/guide/)
- [OpenTelemetry — Python instrumentation](https://opentelemetry.io/docs/languages/python/instrumentation/)
- [Microsoft — Cài ODBC Driver cho SQL Server](https://learn.microsoft.com/en-us/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server)

Địa chỉ trong bộ dữ liệu mẫu chỉ dùng minh họa, cần cập nhật thành địa chỉ tổ chức thực tế. Nguồn của 12 ảnh tài sản được ghi tại [docs/NGUON_ANH.md](docs/NGUON_ANH.md).

Luồng chi tiết của toàn bộ chức năng: [docs/LUONG_CHUC_NANG.md](docs/LUONG_CHUC_NANG.md). Kết quả kiểm chứng cập nhật: [docs/KIEM_THU.md](docs/KIEM_THU.md).

Bản rút gọn dùng hai phương án **Mua mới/Hoãn nhu cầu sử dụng**; chỉ số dựa trên khai báo ban đầu, kết quả sử dụng và xác minh của quản lý. Form nhu cầu/xác minh không có tệp căn cứ; đánh giá vòng đời không bắt buộc căn cứ riêng. Script 004, 005 và 006 cập nhật các CHECK tương ứng, giữ dữ liệu lịch sử. Khi cập nhật database cũ, chạy `.venv\Scripts\python.exe -m backend.app.bootstrap` trước khi mở ứng dụng.

Rà soát tổng thể và các điểm cần cân nhắc: [docs/RA_SOAT_LOGIC.md](docs/RA_SOAT_LOGIC.md).

Trang quản trị có tìm kiếm tự động (hỗ trợ không dấu), lọc tài khoản theo đơn vị/vai trò/trạng thái, lọc danh mục theo trạng thái/đơn vị và lọc chính sách theo hiệu lực. Đổi mục xóa bộ lọc cũ; có số kết quả và Xóa bộ lọc.
