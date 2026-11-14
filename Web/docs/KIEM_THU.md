# Kiểm chứng ENV09 ngày 14/11/2026

| Hạng mục | Kết quả |
|---|---|
| Backend với SQL Server tạm | 65/65 ca đạt |
| Giao diện với Edge và SQL Server tạm | 14/14 kịch bản đạt |
| Kiểm tra mã và dựng frontend | Ruff và TypeScript/Vite đạt |
| SQL Server đang dùng | 13 bảng, 106 cột, 24 khóa ngoại |
| Thiết bị | Kịch bản desktop và điện thoại, kiểm tra kỳ chỉ số từ trình duyệt đặt múi giờ khác |

## Ca hồi quy được rà lại

- Quản trị bị chặn khi gọi trực tiếp API xem lịch sử tài sản hoặc tải tệp nghiệp vụ.
- Nhu cầu mới hoàn trả vẫn chờ khai báo Có hoặc Không mua mới. Máy chủ chặn xác minh sớm. Sửa kết quả đã xác minh yêu cầu đối chiếu lại.
- Khi mở biểu mẫu xác minh mới, quản lý tự đánh dấu dự định mua và mức đáp ứng sau khi đối chiếu. Phương án Hoãn nhu cầu sử dụng khóa lựa chọn dự định mua.
- Bộ lọc chỉ số gửi mốc 00:00 theo giờ Việt Nam dù trình duyệt ở múi giờ khác. Mốc cuối kỳ được loại trừ.
- Thao tác thu hồi, giao nhận cùng phiên bản, duyệt cạnh tranh, hết hạn, quá hạn, bộ lọc quản trị và bố cục điện thoại được chạy lại.

Chạy pytest cho backend và npm run test:ui cho trình duyệt theo [hướng dẫn kiểm thử](../README.md#6-kiểm-thử). Backend tạo và dọn database riêng bằng fixture. Kiểm thử trình duyệt chạy với bản ENV09 đã khởi tạo trên một SQL Server thử. Docker, collector OpenTelemetry và kiểm thử tải chưa được xác nhận trong môi trường này.

## Ghi nhận kiểm thử các phiên bản trước

# Kiểm chứng bản chạy — 07/11/2026

| Hạng mục | Kết quả |
|---|---|
| SQL Server thực tế | `.\MSSQLSERVER08`, database `ENV09`; 12 bảng, 99 cột |
| Kiểm thử backend trên SQL Server riêng | **65/65 đạt** — 30,84 giây |
| Kiểm thử thao tác Edge | **13/13 đạt** — khoảng 1,6 phút |
| React/TypeScript production build | Đạt |
| Ruff và Prettier | Đạt |
| Giao diện | Đã kiểm tra desktop 1440×1000 và điện thoại 390×844 |
| Bản chạy hiện tại | `http://127.0.0.1:8000`, health trả 200 |
| Docker / OpenTelemetry | Có cấu hình, chưa kiểm chứng container hoặc collector ngoài máy |

## Phạm vi kiểm thử

1. Đăng nhập đúng trang vai trò, đổi mật khẩu, thu hồi phiên, CSRF, chặn truy cập khác đơn vị và các thao tác sai quyền. Quản trị chỉ có menu quản trị; bảng tài khoản không hiện email.
2. Thành viên thêm Chờ duyệt; quản lý thêm tự Đang chia sẻ. Người thêm là người phụ trách và không đổi được; chỉ người phụ trách sửa hoặc thu hồi. Duyệt/từ chối dùng popup, không ghi khi đóng popup.
3. Đặt mượn dùng popup; phương án luôn hiện và chỉ có Mua mới/Hoãn nhu cầu sử dụng. Phiếu và khai báo ban đầu cùng giao dịch, gửi lại không nhân đôi; chuẩn hóa thời gian theo độ chính xác giây của SQL.
4. Hai lượt duyệt đồng thời chỉ một lượt thành công; phiếu chờ còn lại tự từ chối đúng lý do. Tài sản đã giữ ẩn khỏi Khám phá, kể cả chọn lịch tương lai. Hủy/hết hạn mở lại nếu còn đủ điều kiện.
5. Giao và trả cần hai người xác nhận cùng phiên bản. Nội dung sửa tăng phiên bản, xóa xác nhận cũ; lưu không đổi giữ xác nhận bên kia. Không giao sớm/hết hạn hoặc giao tài sản cần sửa chữa. Chặn xác nhận khi ảnh/chứng từ còn tải.
6. Thu hồi xóa các phiếu Chờ duyệt/Chờ bàn giao và biên bản chưa hoàn tất. Kiểm tra trực tiếp SQL rằng các dòng đã được xóa; phiếu đã giao/đã đóng và chỉ số liên quan được giữ nguyên.
7. Đang mượn thì Thu hồi chuyển Chờ thu hồi, chưa ẩn hồ sơ đơn vị. Một bên ký trả chưa đủ; đủ hai bên thì tự ẩn, kể cả trả hỏng. Thu hồi trùng lúc xác nhận giao không xóa được phiếu vừa giao xong.
8. Đang có người giữ thì quản lý không thấy nút xử lý vòng đời và API cũng chặn. Người mượn vẫn báo sự cố, nhưng không làm mất yêu cầu Chờ thu hồi.
9. Bỏ trạng thái Tạm ngừng/Ngừng sử dụng. Trả hỏng chuyển Bảo trì; tiếp tục chia sẻ phải ghi tình trạng sau kiểm tra. Không bỏ qua xét duyệt hoặc mở lại hồ sơ đã thu hồi.
10. Bỏ thêm/sửa/gửi nhu cầu riêng khỏi giao diện và API. Nhu cầu chỉ hiện sau hoàn trả; chờ duyệt, hủy, từ chối, đang mượn hoặc mới một bên ký trả chưa được đưa vào danh sách/xác minh.
11. Không tự xác minh, không xác minh nhu cầu chưa hoàn trả, không xác nhận Hoãn nhu cầu sử dụng thành dự định mua mới. Không yêu cầu tệp căn cứ; cập nhật thiếu tệp vẫn giữ tệp lịch sử. Sửa kết quả đã xác minh yêu cầu xác minh lại.
12. Chỉ số đếm nhu cầu đã có lượt hoàn trả; phân biệt đáp ứng mục đích và mua mới thực tế. Bộ dữ liệu thử D=4, A=2, R=50%; D=0 không chia cho 0. Mỗi nhu cầu tính một lần.
13. Quá hạn không tự đóng phiếu; vẫn chặn thêm lượt mượn. Hết hạn nhận chỉ áp dụng trước giao. Tác vụ hết hạn bỏ qua phiếu vừa được thu hồi xóa sau khi chụp danh sách xử lý.
14. Tìm kiếm cập nhật sau 300 ms, dropdown áp dụng ngay; lọc ngày hợp lệ tự tải. Màn hình đang mở tự bỏ dữ liệu khi API trả 403/404 sau thu hồi hoặc thay đổi quyền.
15. Ảnh hiện ngay, xem ảnh/PDF bằng popup tại trang hiện tại; đóng popup con giữ nội dung form. Kiểm tra tệp lỗi, loại tệp, dung lượng, quyền xem tệp và bố cục điện thoại.
16. Quản trị tài khoản, đơn vị có địa chỉ, loại, địa điểm, chính sách; chặn xóa dữ liệu đang được tham chiếu và sửa chính sách đã dùng.

## Nâng cấp và đối chiếu database thật

Đã chạy migration 006 trên ENV09: chuyển Tạm ngừng cũ sang Bảo trì, bỏ Ngừng sử dụng và hỗ trợ Chờ thu hồi. Migration chạy lặp không mất dữ liệu. Không thêm bảng, cột hoặc FK.

Các số lượng trước/sau nâng cấp giữ nguyên: 18 tài sản, 12 phiếu mượn, 10 biên bản, 5 nhu cầu, 4 bản xác minh và 45 sự kiện. Nâng cấp không thực hiện thu hồi thay người dùng hoặc xóa phiếu hiện có.

Kiểm tra giao diện trên ENV09 chỉ đọc và mở/đóng popup; không ghi dữ liệu thử. Các thao tác ghi trong kiểm thử dùng database `ENV09_Test_<UUID>`, tự dọn sau khi chạy. Đã đăng nhập kiểm tra thành viên, quản lý và quản trị trên bản chạy mới.

## Minh chứng

Ảnh trong `docs/anh/`: `booking-with-postponement-mobile.png`, `unified-withdrawal-popup.png`, `lifecycle-two-decisions.png`, `withdrawal-waiting.png`, `needs-after-return.png`, `completed-needs-live.png` và các ảnh giao nhận/quản trị.

Luồng chức năng hiện hành: [LUONG_CHUC_NANG.md](LUONG_CHUC_NANG.md). Các nhận xét nghiệp vụ và đề xuất: [RA_SOAT_LOGIC.md](RA_SOAT_LOGIC.md).

## Bộ lọc quản trị

- Đã thử tìm không dấu/chữ hoa, kết hợp đơn vị + vai trò + trạng thái, Xóa bộ lọc, đổi mục tự xóa lọc và thông báo không có kết quả.
- Đã thử tìm địa chỉ đơn vị, mô tả địa điểm và chính sách theo ba mức hiệu lực. Cập nhật bản ghi trong khi lọc sẽ tự hiện/ẩn theo điều kiện mới.
- Hai kịch bản mới và toàn bộ 11 kịch bản cũ đạt trên database tạm. Không thêm dữ liệu thử vào ENV09.
- Đã xem bản chạy thật trên desktop và 390×844: dropdown đơn vị đủ rộng, bộ lọc không tràn ngang; bảng trên điện thoại cuộn trong bảng.
- Ảnh: admin-filters-live-desktop.png, admin-filters-live-mobile.png và admin-policy-filter.png trong docs/anh. Chỉ thay giao diện, không thêm cột/bảng/FK hoặc đổi API.
