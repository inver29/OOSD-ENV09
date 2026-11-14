# Rà soát logic ENV09

Bản kiểm chứng ngày 14/11/2026 cập nhật điều kiện xác minh, mốc ngày của chỉ số và quyền gọi trực tiếp API nghiệp vụ. Xem [kết quả kiểm thử hiện tại](KIEM_THU.md) và [luồng đang áp dụng](LUONG_CHUC_NANG.md). Cơ sở dữ liệu hiện có 13 bảng, 106 cột và 24 khóa ngoại.

## Ghi nhận rà soát ngày 07/11/2026

Đối chiếu giao diện React, API FastAPI, dịch vụ nghiệp vụ, các CHECK/FK trên SQL Server và bản chạy tại cổng 8000. Kết quả trong phạm vi kiểm tra: chưa phát hiện lỗi chặn các luồng chính sau các sửa đổi dưới đây. Đây là kiểm chứng bản hiện tại trên máy, không phải cam kết mọi tình huống triển khai đều đã được thử.

## 1. Các điểm phát hiện và đã xử lý

| Điểm | Cách xử lý hiện tại |
|---|---|
| Thu hồi và Tạm ngừng chia sẻ chồng chức năng | Chỉ còn Thu hồi tài sản; bỏ nút và API đổi trạng thái chia sẻ riêng. Chỉ người phụ trách được thu hồi. |
| Thu hồi trước giao còn để lại phiếu/biên bản chưa dùng | Hủy và xóa các phiếu Chờ duyệt/Chờ bàn giao cùng biên bản chưa hoàn tất trong một giao dịch. Nhật ký ghi mã phiếu đã xóa. |
| Thu hồi khi đang mượn có thể làm mất luồng trả | Chuyển Chờ thu hồi, giữ phiếu và hồ sơ để trả. Chỉ ẩn sau khi hai bên xác nhận trả cùng phiên bản. |
| Thu hồi đồng thời xác nhận giao có nguy cơ xóa phiếu vừa giao | Khóa tài sản trước phiếu; bên hoàn tất trước quyết định xử lý. Phiếu đã giao luôn được giữ, chuyển sang chờ thu hồi sau trả. |
| Trạng thái Tạm ngừng/Ngừng sử dụng dư so với luồng mới | Loại khỏi UI, API và CHECK trạng thái mới. Tạm ngừng cũ chuyển Bảo trì; Ngừng sử dụng cũ chuyển thu hồi, giữ lịch sử. |
| Quản lý còn thao tác vòng đời khi người mượn chưa trả | Ẩn nút và chặn tại API. Người mượn vẫn báo sự cố; báo sự cố không xóa yêu cầu Chờ thu hồi. |
| Thêm nhu cầu riêng không phù hợp yêu cầu tự sinh sau hoàn trả | Bỏ form, nút và API thêm/sửa/gửi nhu cầu riêng. Lưu khai báo ban đầu lúc đặt mượn nhưng chỉ đưa vào danh sách/xác minh sau khi hoàn trả xong. |
| Nhu cầu chưa hoàn trả vẫn có thể vào bộ đếm/xác minh | Danh sách, chi tiết, khai báo kết quả, xác minh, thẻ Tổng quan và mẫu tính chỉ số đều kiểm tra đã có phiếu hoàn trả. |
| Thời gian có phần mili giây khác độ chính xác SQL gây lỗi đặt mượn hợp lệ | Chuẩn hóa đầu vào theo giây, thống nhất với DATETIMEOFFSET(0). Đã thử gửi lại cùng yêu cầu có mili giây. |
| Màn hình khác còn giữ nội dung/điều khiển cũ sau thu hồi | Khi tải lại nhận 403/404, bỏ dữ liệu cũ và điều khiển. Có kiểm thử hai phiên: người phụ trách thu hồi, màn hình quản lý đang mở tự cập nhật. |
| Tác vụ hết hạn gặp phiếu vừa được thu hồi xóa | Bỏ qua phiếu không còn tồn tại sau khi lấy danh sách; không gây lỗi cho toàn bộ lượt chạy. |
| Có thể xác nhận giao nhận trong lúc ảnh/chứng từ chưa tải xong | Khóa thao tác lưu/xác nhận trong lúc tải. Kiểm thử cố tình trì hoãn upload để xác nhận nút bị khóa. |

Các yêu cầu căn cứ riêng đã bỏ khỏi form; dữ liệu đính kèm lịch sử vẫn được giữ. Nhãn lựa chọn hiện là **Mua mới** và **Hoãn nhu cầu sử dụng**.

## 2. Đối chiếu các chức năng

| Nhóm chức năng | Kết quả kiểm tra |
|---|---|
| Đăng nhập, đăng xuất, đổi mật khẩu | Đúng trang theo vai trò; tài khoản/quyền bị đổi được kiểm tra lại; có CSRF cho thao tác ghi. |
| Quản trị | Có tài khoản, đơn vị/địa chỉ, địa điểm, loại, chính sách; chặn dữ liệu trùng và xóa mục đang tham chiếu. Quản trị chỉ có trang quản trị. |
| Đăng ký, xét duyệt tài sản | Thành viên thêm Chờ duyệt; quản lý thêm tự duyệt. Từ chối có lý do; người phụ trách sửa rồi gửi lại. |
| Khám phá và đặt mượn | Chỉ chia sẻ giữa đơn vị khác nhau; kiểm tra lịch, thời hạn, chính sách, tình trạng và danh mục. Phiếu và phương án nhu cầu được ghi cùng giao dịch. |
| Duyệt, hủy, hết hạn nhận | Duyệt khóa lịch và từ chối các phiếu chờ khác đúng lý do. Hủy/hết hạn chỉ trước giao; không tự hủy trách nhiệm người đang giữ. |
| Giao nhận | Hai tài khoản khác nhau, cùng phiên bản; sửa nội dung phải ký lại; đủ xác nhận mới chuyển trạng thái. |
| Hoàn trả, quá hạn | Đủ xác nhận mới đóng phiếu. Trả hỏng chuyển Bảo trì; Chờ thu hồi thì tự ẩn. Quá hạn là cảnh báo, không tự đóng. |
| Vòng đời | Chỉ xử lý khi không còn người giữ; hai quyết định Tiếp tục chia sẻ/Bảo trì. Không mở lại hồ sơ đã thu hồi hoặc bỏ qua xét duyệt đăng ký. |
| Nhu cầu và xác minh | Không thêm riêng. Sau trả tự hiện, khai báo kết quả và quản lý đơn vị mượn xác minh; cấm tự xác minh. |
| Chỉ số tránh mua mới | D chỉ gồm nhu cầu đã có lượt hoàn trả và được xác minh dự định mua; A yêu cầu đáp ứng mục đích và không mua mới. Đếm một lần, D=0 không chia. |
| Ảnh, chứng từ, tìm kiếm | Xem bằng popup; ảnh chọn hiện ngay; kiểm tra tệp/quyền xem; tìm kiếm và dropdown tự tải. |
| SQL và thao tác đồng thời | Khóa theo tài sản → phiếu → biên bản; lỗi hoàn tác. Thu hồi không làm đứt FK của phiếu đã giao/đã đóng. |

Quy tắc chỉ một phiếu được duyệt/đang mượn cho một hiện vật, kể cả đặt lịch tương lai, đang áp dụng theo lựa chọn đơn giản hóa trước đó của bạn. Đây là giới hạn nghiệp vụ chủ động, không phải thuật toán xếp nhiều lịch liên tiếp.

## 3. Các điểm cần cân nhắc và phương án đề xuất

### Một quản lý mỗi chi nhánh và quy tắc không tự xác minh

Database hiện có một quản lý hoạt động tại mỗi chi nhánh. Quản lý vẫn có thể mượn ở chi nhánh khác, nhưng nhu cầu do chính họ lập không được tự xác minh. Nếu không có quản lý thứ hai, phần xác minh của nhu cầu này sẽ chờ.

Đề xuất: nếu muốn quản lý sử dụng đầy đủ chức năng mượn và tính chỉ số, cấp thêm một quản lý khác cùng chi nhánh để xác minh độc lập. Nếu muốn giữ ít tài khoản, quy ước thành viên là người lập phiếu, quản lý thực hiện duyệt/giao nhận/xác minh. Chưa tự đổi quyền hoặc thêm tài khoản vào database.

### Phạm vi của chỉ số đã hẹp hơn đề xuất ban đầu

Theo yêu cầu chỉ hiện nhu cầu sau hoàn trả, chỉ số chỉ đánh giá các lượt mượn đã hoàn tất; không còn bao gồm nhu cầu chưa mượn được. Tỷ lệ vì vậy không đại diện cho toàn bộ khả năng giảm mua mới của công ty. Phương án Mua mới là khai báo trước lúc mượn, không còn bắt buộc chứng từ dự định mua.

Đề xuất: giữ phạm vi này cho đồ án gọn, nhưng ghi đúng giả định trong báo cáo và phần thuyết trình. Website đã nêu phạm vi trong mô tả và giả định chỉ số. Chưa cập nhật file Word/draw.io trong lần sửa website này.

### Ba nhu cầu cũ chưa có phiếu hoàn trả

ENV09 có 5 nhu cầu, trong đó 2 nhu cầu gắn phiếu đã hoàn trả. Ba hồ sơ còn lại được giữ trong database để bảo toàn khai báo/lịch sử cũ, nhưng không hiện ở danh sách/xác minh hoặc góp vào chỉ số mới. Không chuyển chúng thành lượt đã hoàn trả để tạo dữ liệu đẹp.

Đề xuất: giữ dưới dạng dữ liệu lưu trữ; chỉ dọn khi đã đối chiếu xong báo cáo và xác định hồ sơ nào là dữ liệu thử. Việc nâng cấp hiện tại không xóa các hồ sơ cũ này.

### Hồ sơ tài sản được ẩn, phiếu đang chờ được xóa thật

Thu hồi xóa thật các phiếu còn chờ và biên bản chưa hoàn tất theo yêu cầu. Bản ghi tài sản được đánh dấu thu hồi, giữ lại để phiếu/biên bản đã giao nhận và chỉ số còn đối chiếu được. Người dùng không thấy tài sản đã thu hồi trên các trang tài sản.

Đề xuất: giữ cách này để không làm mất lịch sử. Không xóa dây chuyền tài sản đã có chứng từ hoàn tất.

## 4. Bằng chứng và giới hạn kiểm chứng

- 65 kiểm thử backend đạt trên SQL Server tạm, gồm quyền, đồng thời, hoàn tác, thu hồi, tự hiện nhu cầu, ràng buộc và migration.
- 13 kịch bản Edge đạt, gồm các luồng xuyên vai trò và màn hình desktop/điện thoại. Production build, Ruff và Prettier đạt.
- Migration trên ENV09 giữ số dòng: 18 tài sản, 12 phiếu, 10 biên bản, 5 nhu cầu, 4 bản xác minh, 45 sự kiện. Không thêm bảng/cột/FK.
- Bản chạy mới đã kiểm tra trực tiếp bằng ba vai trò, health 200; kiểm tra trực tiếp không ghi dữ liệu thử.
- Chưa chạy thử tải lớn, triển khai công khai, Docker hoặc collector OpenTelemetry. Phiên hiện dùng bộ nhớ một tiến trình, khởi động lại yêu cầu đăng nhập lại.

Luồng chi tiết: [LUONG_CHUC_NANG.md](LUONG_CHUC_NANG.md). Kết quả và ảnh: [KIEM_THU.md](KIEM_THU.md).
