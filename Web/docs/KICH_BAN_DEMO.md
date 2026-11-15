# Kịch bản demo website ENV09

Demo cách hai chi nhánh chia sẻ tài sản và theo dõi việc mượn có giúp tránh mua mới hay không. Dành khoảng 12–15 phút cho luồng chính và 25–35 phút nếu trình bày cả các trường hợp bổ sung.

## 1. Chuẩn bị trước khi trình bày

Dùng một database demo riêng để có đúng tài khoản, tài sản và phiếu mẫu trong kịch bản. Chạy khối lệnh sau trong PowerShell của VS Code.

```powershell
Set-Location 'C:\Study\OSSD_CK\OOSD-ENV09\Web'
$env:APP_DB_NAME = 'ENV09_DemoBaoVe'
$env:APP_STORAGE_DIR = Join-Path $env:LOCALAPPDATA 'ENV09_DemoBaoVe\uploads'
$env:APP_EXPIRY_WORKER = 'true'
.\.venv\Scripts\python.exe -m backend.app.bootstrap --seed
if ($LASTEXITCODE -ne 0) { throw 'Khởi tạo database demo thất bại.' }
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8010
```

Các lệnh dùng thư viện đã cài và bản giao diện đã build trong `frontend/dist`. Nếu chưa có bản build, chạy `npm.cmd run build` từ thư mục `Web/frontend` trước. Giữ terminal chạy và mở [ENV09 demo](http://127.0.0.1:8010). Lệnh nạp mẫu chỉ thêm dữ liệu vào database chưa có tài khoản. Nếu đã dùng tên trên để tập demo, đổi tên database và thư mục ảnh đều sang `ENV09_DemoBaoVe2` để bắt đầu lại với bộ mẫu ban đầu.

Mật khẩu của các tài khoản mẫu là giá trị `APP_DEMO_PASSWORD` trong `Web/.env` tại thời điểm nạp dữ liệu. Chuẩn bị một ảnh PNG hoặc JPG dưới 8 MB. Tên tài sản tạo trong buổi demo bắt đầu bằng `DEMO -` để dễ tìm.

| Tài khoản | Vai trò trong buổi demo |
|---|---|
| `an` | Thành viên TP.HCM, đăng ký tài sản và nhận thông báo trong các tình huống bổ sung |
| `chi` | Thành viên Hà Nội, người mượn trong luồng chính |
| `binh` | Thành viên Đà Nẵng, gửi yêu cầu cạnh tranh và báo sự cố |
| `ql.hcm` | Quản lý TP.HCM, duyệt tài sản, duyệt phiếu và giao nhận trong luồng chính |
| `ql.hn` | Quản lý Hà Nội, xác minh nhu cầu của Chi và xử lý các phiếu mẫu Hà Nội |
| `ql.dn` | Quản lý Đà Nẵng, xử lý phiếu từ chối thủ công và phiếu hết hạn nhận |
| `admin` | Quản trị tài khoản và danh mục |

Giữ hai phiên đăng nhập trên **hai hồ sơ trình duyệt riêng** hoặc **một cửa sổ thường và một cửa sổ InPrivate**. Có thể dùng phiên thứ ba cho Bình. Các tab mở trong cùng hồ sơ trình duyệt dùng chung phiên đăng nhập. Sau thao tác ở cửa sổ này, bấm **Làm mới** hoặc tải lại ở cửa sổ kia để thấy kết quả ngay.

## 2. Luồng chính để trình bày

**Lời mở đầu**

> Em sẽ dùng tài sản của chi nhánh TP.HCM cho một buổi đào tạo ở Hà Nội. Quản lý TP.HCM duyệt và giao nhận. Quản lý Hà Nội xác minh hiệu quả sử dụng sau khi trả.

### Bước 1. Đăng ký, từ chối, sửa và duyệt tài sản

1. `an` đăng nhập, chỉ nhanh trang **Tổng quan**, rồi vào **Tài sản đơn vị → Đăng ký tài sản**. Nhập tên `DEMO - Máy chiếu đào tạo`, loại **Thiết bị trình chiếu**, địa điểm **Kho thiết bị**, tình trạng `Hoạt động tốt, đầy đủ phụ kiện.`. Chọn ảnh và chỉ phần xem trước. Bấm **Thêm**. Tài sản hiện **Chờ duyệt**, người phụ trách là Nguyễn An.
2. `ql.hcm` vào **Tài sản đơn vị**, gõ `DEMO - Máy chiếu đào tạo` và mở **Xét duyệt tài sản**. Chọn **Từ chối**, nhập `Vui lòng bổ sung dây HDMI và điều khiển.`. Chỉ trạng thái **Từ chối** và lý do trên hồ sơ.
3. `an` mở lại tài sản → **Sửa hồ sơ** → điền **Đặc tính / Phụ kiện** là `Kèm dây HDMI và điều khiển.` → **Gửi lại duyệt**. `ql.hcm` mở lại hộp thoại và chọn **Duyệt**. Tài sản chuyển **Đang chia sẻ**. Chỉ trên hồ sơ rằng quản lý xét duyệt còn An có quyền sửa và thu hồi.

### Bước 2. Tra cứu, đặt mượn và xét duyệt phiếu

1. `chi` vào **Khám phá tài sản**. Gõ `Máy chiếu đào tạo`, chọn loại **Thiết bị trình chiếu** hoặc đơn vị **Chi nhánh TP. Hồ Chí Minh**. Chỉ kết quả đổi ngay. Mở thẻ tài sản, xem ảnh, nơi giao nhận, địa chỉ và **Lịch đã giữ**. Có thể mở **Lọc theo lịch** để chọn hai mốc và xem kết quả lọc.
2. Bấm **Đặt mượn tài sản**. Chọn **Nhận từ** khoảng 4–5 phút sau giờ hiện tại và **Trả trước** là ngày mai. Nhập mục đích `Dùng máy chiếu cho buổi đào tạo nội bộ.`, chọn **Mua mới** nếu không mượn được, rồi **Gửi yêu cầu**. Ghi lại mã phiếu hiển thị. Phiếu ở **Chờ duyệt**. Mở **Phiếu mượn của tôi → Nhu cầu sử dụng** để chỉ rằng nhu cầu mới chưa xuất hiện.
3. `binh` gửi thêm một yêu cầu cho **cùng máy chiếu** trước khi quản lý duyệt. Dùng cùng khoảng thời gian, mục đích `Chiếu nội dung cuộc họp chi nhánh.` và phương án **Hoãn nhu cầu sử dụng**.
4. `ql.hcm` vào **Xử lý mượn–trả → Chờ duyệt**, tìm theo tên máy chiếu, bấm **Xét duyệt** đúng dòng có người mượn **Lê Chi**. Đối chiếu đơn vị, thời gian, mục đích và lịch, rồi bấm **Duyệt**. Phiếu Chi chuyển **Chờ bàn giao**, phiếu Bình chuyển **Từ chối** với lý do **Đã có người khác mượn tài sản này**. Tải lại **Khám phá tài sản** để thấy máy chiếu đã ẩn trong thời gian giữ.

### Bước 3. Bàn giao, chứng từ và hoàn trả

1. Đến giờ **Nhận từ**, `ql.hcm` vào **Xử lý mượn–trả → Chờ bàn giao**, mở phiếu của Chi → **Bàn giao tài sản**. Chọn **Đạt**, nhập `Đã kiểm tra máy chiếu, dây HDMI và điều khiển.`. Gắn ảnh nếu muốn minh họa chứng từ, rồi **Xác nhận bàn giao**. Chỉ biên bản đã có xác nhận bên giao và phiếu vẫn **Chờ bàn giao**.
2. `chi` mở lại phiếu. Nếu đã gắn ảnh, bấm **Xem ảnh / Chứng từ** để mở hộp xem. Bấm **Đã nhận tài sản**. Phiếu chuyển **Đang mượn**, tài sản hiện **Đã được mượn** ở phía quản lý.
3. `chi` bấm **Trả tài sản**, chọn **Đạt**, nhập `Đã trả máy chiếu và đầy đủ phụ kiện.`, chọn quản lý TP.HCM nếu ô chọn xuất hiện rồi **Xác nhận trả tài sản**. Phiếu chuyển **Chờ xác nhận trả**.
4. `ql.hcm` mở lại đúng phiếu, kiểm tra biên bản rồi **Xác nhận đã nhận trả**. Phiếu chuyển **Đã hoàn trả**, biên bản có đủ hai xác nhận. Giờ dự phòng tính từ lúc nhận trả thực tế. Trên trang **Phiếu mượn của tôi → Nhu cầu sử dụng** của Chi, nhu cầu dùng máy chiếu tự xuất hiện.

Nếu chưa tới giờ nhận, tận dụng thời gian để trình bày việc từ chối phiếu Bình, bộ lọc hoặc trang quản trị. Nếu buổi demo quá ngắn, dùng phiếu **Màn hình Dell 24 inch** của An trong database vừa nạp để trình bày thao tác giao ngay với `ql.hn`. Sau đó dùng dữ liệu đã hoàn trả của Chi để trình bày chỉ số.

### Bước 4. Khai báo kết quả, xác minh và xuất CSV

1. `chi` mở phiếu vừa hoàn trả. Ở **Nhu cầu & kết quả sử dụng**, chọn **Không mua mới** và bấm **Lưu kết quả**.
2. Đăng nhập `ql.hn` và vào **Hiệu quả sử dụng → Xác minh nhu cầu**. Tìm `Dùng máy chiếu cho buổi đào tạo nội bộ`, mở hồ sơ rồi bấm **Xác minh kết quả**. Chọn **Chấp nhận kết quả xác minh**, **Xác nhận dự định mua mới ban đầu** và **Việc mượn đã đáp ứng mục đích sử dụng**. Nhập `Đã đối chiếu biên bản trả và xác nhận đơn vị không mua mới.` → **Xác nhận**. Hệ thống hiển thị **Đã xác minh**.
3. Vào tab **Chỉ số tránh mua mới**. Đặt **Từ ngày** cách hôm nay khoảng 45 ngày, **Đến trước ngày** là ngày sau mốc trả dự kiến, chọn **Mọi loại tài sản**. Trên database mới nạp, trước khi xác minh lượt demo có **A = 2, D = 4**, sau đó có **A = 3, D = 5 → 60%**. Đổi bộ lọc sang **Thiết bị trình chiếu** để thấy cần một hiện vật và đã tránh mua một hiện vật, tức **1/1 = 100%**. Bấm **Xuất CSV** và mở tệp vừa tải.
4. Nếu được hỏi vì sao hai quản lý khác nhau, giải thích rằng quản lý TP.HCM phụ trách duyệt và giao nhận tài sản của đơn vị mình. Quản lý Hà Nội đối chiếu nhu cầu của đơn vị mượn. Tỷ lệ tính trên các nhu cầu đủ điều kiện và được xác minh trong kỳ.

## 3. Các tình huống bổ sung để demo đủ chức năng

| Chức năng | Thao tác demo | Kết quả cần chỉ |
|---|---|---|
| Quản lý đăng ký tài sản | `ql.hcm` đăng ký `DEMO - Webcam thu hồi`, loại **Máy ảnh & ghi hình**, kho thiết bị, tình trạng **Tốt**. | Tài sản **Đang chia sẻ** ngay và quản lý là người phụ trách. Dùng tài sản này cho tình huống thu hồi bên dưới. |
| Từ chối phiếu thủ công | `an` gửi một phiếu cho **Máy ảnh Sony ZV-E10** của Đà Nẵng. `ql.dn` mở **Xử lý mượn–trả → Chờ duyệt → Xét duyệt → Từ chối**, nhập `Thiết bị cần ưu tiên dùng tại đơn vị.`. | Phiếu **Từ chối** và người mượn thấy lý do. |
| Hủy phiếu trước giao | `an` gửi phiếu mượn mới cho **Máy chiếu Epson EB-X49**, dùng mục đích `Demo tình huống hủy trước giao.` để phân biệt với phiếu có sẵn. `ql.hn` duyệt đúng phiếu mới. An mở chi tiết → **Hủy phiếu**, nhập `Lịch họp đã thay đổi.` rồi xác nhận. | Phiếu mới **Đã hủy** được giữ để tra cứu. Tài sản xuất hiện lại khi đủ điều kiện chia sẻ. |
| Hết hạn nhận | `an` mượn **Màn hình LG 27 inch** ở Đà Nẵng. Chọn **Nhận từ** sau khoảng 1–2 phút, **Trả trước** sau khoảng 4–5 phút. `ql.dn` duyệt trước mốc trả và để phiếu ở **Chờ bàn giao** trong khi trình bày chức năng khác. | Sau mốc trả và một lượt kiểm tra định kỳ khoảng 30 giây, phiếu thành **Hết hạn nhận**. Tài sản đủ điều kiện xuất hiện lại. |
| Sửa, hủy và mở lại biên bản | Làm ngay sau khi `ql.hcm` ký giao máy chiếu ở bước 3, trước khi Chi bấm **Đã nhận tài sản**. Quản lý chọn **Chỉnh sửa biên bản**, thêm câu **Đã kiểm tra dây HDMI** và xác nhận. Nếu cần, thử **Hủy biên bản → Mở lại biên bản → Xác nhận bàn giao**. | Phiên bản tăng khi nội dung đổi. Người mượn đọc bản mới rồi xác nhận. Hủy biên bản giữ phiếu ở **Chờ bàn giao**. |
| Báo sự cố và bảo trì | `binh` mở phiếu đang mượn **Laptop Lenovo ThinkPad E14** → **Báo sự cố**, nhập `Cổng HDMI không nhận tín hiệu.` → **Gửi sự cố**. Bình thực hiện **Trả tài sản**, chọn **Hư hỏng** rồi chuyển sang `ql.hn` để xác nhận đã nhận trả. | Khi Bình đang giữ, quản lý xem được hồ sơ. Nút đánh giá vòng đời chỉ khả dụng sau khi nhận trả. Phiếu đã trả và laptop chuyển **Bảo trì**. |
| Đánh giá và chia sẻ lại | `ql.hn` mở Lenovo trong **Tài sản đơn vị → Xử lý & đánh giá vòng đời**. Ở **Loại ghi nhận**, chọn **Xử lý & đánh giá**, nhập nội dung `Đã kiểm tra và sửa cổng HDMI.`, quyết định **Tiếp tục chia sẻ**, tình trạng sau kiểm tra `Hoạt động tốt sau khi sửa.` → **Lưu thay đổi**. | Tài sản chuyển **Đang chia sẻ** và kết quả có trong **Lịch sử vòng đời**. Có thể mở lại form để chỉ lựa chọn **Bảo trì**. |
| Thu hồi trước giao và đọc thông báo | `chi` đặt mượn **DEMO - Webcam thu hồi**, chọn thời gian tương lai. Có thể để phiếu **Chờ duyệt** hoặc duyệt thành **Chờ bàn giao**. `ql.hcm` mở hồ sơ webcam → **Thu hồi tài sản** và xác nhận. Chi tải lại rồi mở chuông **Thông báo**. | Webcam ẩn, phiếu chưa giao biến mất. Chuông còn mã phiếu và lý do **Người phụ trách đã thu hồi tài sản**. Bấm **Đánh dấu đã đọc**. |
| Quá hạn trả và thu hồi khi còn người giữ | `an` mở phiếu **Máy ảnh Canon EOS M50** có nhãn **Quá hạn trả** trong bộ mẫu. `ql.hn` mở tài sản và **Thu hồi tài sản**, rồi để An bấm **Trả tài sản** và hoàn tất cùng quản lý. Nếu bộ mẫu đã có biên bản trả đang chờ ký, mở biên bản đang có và xác nhận theo đúng bên. | Trong lúc chờ, tài sản ở **Chờ thu hồi** và phiếu vẫn xử lý được. Khi đủ hai xác nhận trả, tài sản ẩn và phiếu **Đã hoàn trả** vẫn tra cứu được. |
| Đổi kết quả sau xác minh | `chi` mở nhu cầu máy chiếu đã xác minh, đổi sang **Có mua mới** và lưu. Sau khi minh họa, đổi lại **Không mua mới** rồi để `ql.hn` xác minh lại. | Nhu cầu quay về **Chờ xác minh**, tạm rời kỳ chỉ số cho đến lúc xác minh lại. |
| Từ chối xác minh | `ql.hn` mở lại nhu cầu máy chiếu sau khi Chi khai báo kết quả. Bấm **Xác minh kết quả**, bỏ chọn **Chấp nhận kết quả xác minh**, nhập `Cần đối chiếu thêm việc mua mới của đơn vị.` rồi **Xác nhận**. | Nhu cầu ở **Từ chối** và rời danh sách đối chiếu của kỳ. `ql.hn` có thể xác minh lại khi đã đối chiếu đủ thông tin. |

## 4. Quản trị và tài khoản

1. Đăng nhập `admin`. Website mở thẳng **Quản trị hệ thống → Tài khoản & cấu hình**. Gõ `ql` vào ô tìm kiếm, chọn **Quản lý tài sản** và một đơn vị để chỉ các bộ lọc kết hợp. Thử **Xóa bộ lọc**, rồi chuyển tab.
2. Tab **Đơn vị → Thêm đơn vị**. Nhập `DEMO - Chi nhánh thử` và địa chỉ `25 Nguyễn Văn Linh, TP. Hồ Chí Minh`. Mở nút sửa của dòng để đổi địa chỉ nếu cần demo cập nhật.
3. Tab **Địa điểm → Thêm địa điểm**, nhập `DEMO - Kho thử` và chọn đơn vị vừa tạo. Tab **Loại tài sản → Thêm loại tài sản**, nhập `DEMO - Thiết bị đo`. Có thể xóa thử hai mục này khi chúng chưa được sử dụng. Xóa địa điểm trước khi xóa đơn vị vừa tạo.
4. Tab **Tài khoản → Tạo tài khoản**. Nhập họ tên `Tài khoản trình diễn`, tên đăng nhập `demo.baove`, email `demo.baove@env09.example`, chọn **Chi nhánh Hà Nội**, vai trò **Thành viên** và mật khẩu tự đặt từ 8 ký tự. Có thể dùng nút sửa để cập nhật họ tên hoặc trạng thái.
5. Tab **Chính sách mượn → Thêm chính sách**. Nhập `Phiên bản chính sách demo`, **10 ngày mượn**, **2 giờ dự phòng**, **12 giờ chờ nhận**, **hiệu lực sau 7 ngày**. Lọc **Chưa đến hiệu lực** để thấy dòng vừa tạo và thử sửa một giá trị. Chính sách đang dùng vẫn áp dụng cho các phiếu trong buổi demo.
6. Dùng một cửa sổ riêng đăng nhập `demo.baove`. Mở menu tài khoản → **Đổi mật khẩu**, nhập mật khẩu hiện tại và mật khẩu mới. Đăng nhập lại với mật khẩu mới, rồi **Đăng xuất**. Nếu muốn minh họa khóa tài khoản, quay về quản trị, sửa tài khoản thử và bỏ dấu **Đang hoạt động**, sau đó thử đăng nhập lại.

## 5. Nếu được hỏi về SQL hoặc điện thoại

- Dùng F12 và chế độ thiết bị để mở **Khám phá tài sản** ở kích thước điện thoại. Chỉ menu thu gọn, danh sách dạng thẻ và hộp thoại đặt mượn.
- Đối chiếu phiếu vừa demo với SQL Server. Thay `9` bằng mã phiếu bạn vừa thấy trên web, ví dụ `9` tương ứng `PM-0009`. Chọn đúng database demo trong SSMS.

```sql
USE ENV09_DemoBaoVe;
SELECT MaPhieuMuon, MaTaiSan, MaNguoiMuon, TrangThai,
       DuyetLuc, GiaoLuc, TraLuc
FROM dbo.PhieuMuon
WHERE MaPhieuMuon = 9;
```

- Khi phiếu hoàn tất trả, web hiển thị **Đã hoàn trả**, SQL lưu `DA_HOAN_TRA`. Hai bản ghi biên bản trong `BienBanGiaoNhan` đối chiếu theo `MaPhieuMuon` và có loại `GIAO` hoặc `TRA`. Hệ thống tính **Quá hạn trả** từ hạn trả và trạng thái đang giữ.

**Lời kết**

> Qua lượt mượn vừa rồi, em có thể đối chiếu người phụ trách tài sản, người duyệt, xác nhận giao nhận của hai bên và kết quả tránh mua mới. Khi hủy, hết hạn hoặc thu hồi, hệ thống giải phóng lịch còn giữ. Riêng khi tài sản bị thu hồi, người mượn liên quan nhận thông báo kèm lý do.
