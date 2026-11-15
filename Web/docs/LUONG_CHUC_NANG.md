# Luồng hoạt động các chức năng ENV09

Đối chiếu với mã backend, giao diện và các kiểm thử ngày 07/11/2026. Các địa chỉ và ảnh có sẵn là dữ liệu minh họa; không thay thế ảnh hiện trạng khi giao nhận.

**Luồng mượn hoàn chỉnh:** Thành viên khám phá tài sản → xem chi tiết và lịch → gửi yêu cầu → quản lý đơn vị sở hữu duyệt → quản lý ghi nội dung và xác nhận bàn giao → người mượn xác nhận đã nhận → đang mượn → người mượn ghi tình trạng và xác nhận trả → quản lý kiểm tra và xác nhận đã nhận trả → đóng phiếu → giữ giờ dự phòng sau trả.

**Hai phạm vi quản lý:** Quản lý đơn vị sở hữu tài sản duyệt, bàn giao và nhận trả. Quản lý đơn vị có nhu cầu sử dụng xác minh kết quả tránh mua mới; được xem phiếu liên kết để đối chiếu nhưng không duyệt hoặc xác nhận thay đơn vị sở hữu.

## 1. Đăng nhập, trang vào và Tổng quan

1. Người dùng nhập tài khoản, mật khẩu và chọn Đăng nhập.
2. Hệ thống kiểm tra mật khẩu, trạng thái tài khoản và đơn vị.
3. Thành viên và quản lý vào **Tổng quan**, kể cả khi trước đăng nhập đang mở một đường dẫn khác. Quản trị vào thẳng **Quản trị hệ thống** và chỉ có menu quản trị.
4. Thành viên xem tài sản đang chia sẻ, phiếu đang mở, đang mượn và quá hạn. Quản lý xem yêu cầu chờ duyệt, phiếu quá hạn, nhu cầu chờ xác minh và tài sản cần xử lý.
5. Chọn chỉ số hoặc phiếu gần đây để mở danh sách/chi tiết tương ứng. Tài khoản hoặc đơn vị bị khóa không được đăng nhập.

## 2. Thêm, xét duyệt và thu hồi tài sản

Thành viên → Tài sản đơn vị → Đăng ký tài sản → nhập tên, loại, địa điểm, tình trạng, đặc tính và ảnh → **Thêm** → **Chờ duyệt**. Tài sản chưa xuất hiện cho đơn vị khác đặt mượn. Người thêm luôn là người phụ trách; trường này chỉ đọc, API cũng không cho đổi.

Quản lý chi nhánh thực hiện cùng form → Thêm → tự động duyệt thành **Đang chia sẻ**, không cần duyệt lại. Chọn ảnh sẽ có xem trước ngay; chờ tải ảnh xong mới lưu hồ sơ.

Quản lý đúng chi nhánh → mở tài sản Chờ duyệt → **Xét duyệt tài sản → Duyệt** ngay trên thẻ tài sản (hoặc Duyệt ở trang chi tiết) → **Đang chia sẻ**; hoặc **Từ chối → nhập lý do → Từ chối**. Thành viên không được tự duyệt; chi nhánh khác không được duyệt thay. Không mở chia sẻ tài sản Chờ duyệt qua chức năng đánh giá vòng đời.

Chỉ người phụ trách → mở hồ sơ → **Thu hồi tài sản → Thu hồi tài sản** trong popup. Các phiếu còn Chờ duyệt/Chờ bàn giao được hủy và xóa khỏi database cùng biên bản chưa hoàn tất. Nhu cầu ban đầu vẫn được giữ nhưng không hiện nếu chưa có lượt hoàn trả; lịch sử thu hồi ghi các mã phiếu đã xóa.

Nếu chưa có người giữ, tài sản ẩn ngay khỏi danh sách và đường dẫn hồ sơ. Nếu đã có người mượn, tài sản chuyển **Chờ thu hồi**, vẫn hiện ở Tài sản đơn vị và trên phiếu để hoàn trả. Không cho mượn mới, sửa hồ sơ hay xử lý vòng đời trong lúc chờ. Sau khi hai bên hoàn tất biên bản Trả, tài sản tự ẩn. Phiếu/biên bản đã giao nhận được giữ để tra cứu và tính chỉ số. Không có chức năng khôi phục trên web.

Lý do tự động khi thu hồi: **Người phụ trách đã thu hồi tài sản**. Phiếu còn đang mượn hiển thị lý do này và giữ nội dung xử lý trước đó nếu có. Các phiếu chờ bị xóa thì lý do được ghi trong lịch sử thu hồi tài sản.

## 3. Sửa hồ sơ tài sản

Chỉ đúng người phụ trách thuộc đơn vị sở hữu được sửa tài sản chưa thu hồi hoặc Chờ thu hồi; quyền quản lý không cho phép sửa hoặc thu hồi thay người phụ trách. Tài sản bị từ chối → Sửa hồ sơ → bổ sung thông tin → **Gửi lại duyệt** → trở về Chờ duyệt. Sau duyệt, người phụ trách vẫn được chỉnh sửa hồ sơ, có kiểm tra phiên bản và các ràng buộc lịch sử.

Nếu người khác đã cập nhật, hệ thống yêu cầu tải lại. Tài sản đã có phiếu mượn không đổi loại; người phụ trách là người tạo và không được thay đổi. Tài sản đã thu hồi không xem/sửa/duyệt/ghi nhận vòng đời được. Ghi nhận vòng đời áp dụng sau khi tài sản đã được duyệt.

## 4. Khám phá tài sản và kiểm tra lịch

Thành viên/quản lý → Khám phá tài sản → nhập từ khóa (tự tìm sau 300 ms), chọn loại/đơn vị (áp dụng ngay) → có thể chọn Lọc theo lịch, nhập đủ hai mốc thời gian hợp lệ để tự lọc lịch trống → mở tài sản.

Trang chi tiết hiển thị đặc tính, tình trạng, người phụ trách, email, địa điểm, địa chỉ đơn vị và lịch đã giữ, kể cả giờ dự phòng. Kết quả mặc định là tài sản đang chia sẻ của **đơn vị khác**, chưa có phiếu đã duyệt/đang mượn. Tài sản Chờ bàn giao hoặc Đã được mượn được ẩn, kể cả chọn lịch ở tương lai. Nhãn Đang chia sẻ không có nghĩa hiện vật đang trống ngay lúc xem; cần đối chiếu lịch. Tra cứu không giữ chỗ.

## 5. Gửi yêu cầu mượn

Thành viên → chi tiết tài sản → Đặt mượn tài sản → popup nhập nhận từ/trả trước/mục đích và lựa chọn **Mua mới** hoặc **Hoãn nhu cầu sử dụng** nếu không mượn được → Gửi yêu cầu. Phần lựa chọn luôn hiển thị, không có dropdown Ghi nhận nhu cầu sử dụng và không đính kèm căn cứ dự định mua. Hệ thống tự ghi nhu cầu theo loại tài sản, thời gian, mục đích và phương án trong cùng giao dịch với phiếu; lỗi sẽ hoàn tác cả hai.

Hệ thống kiểm tra thời gian, thời hạn tối đa, khác đơn vị, tình trạng chia sẻ, danh mục, người phụ trách và xung đột lịch. Nhu cầu liên kết phải đúng loại tài sản, cùng đơn vị mượn và bao trùm thời gian mượn. Lưu thành công tạo phiếu **Chờ duyệt**, hiển thị trong Phiếu mượn của tôi và danh sách quản lý đơn vị sở hữu. Chờ duyệt chưa giữ lịch; gửi lại cùng yêu cầu không tạo hai phiếu.

## 6. Xét duyệt hoặc từ chối

Quản lý đơn vị sở hữu → Xử lý mượn–trả → tab Chờ duyệt → Xét duyệt tại dòng phiếu → đối chiếu người mượn, mục đích, thời gian và lịch → Duyệt. Ở trang chi tiết, Duyệt/Từ chối mở popup xác nhận; dữ liệu chỉ đổi sau khi xác nhận trong popup. Danh sách đã mở popup xét duyệt nên không chồng thêm popup khác.

Hệ thống kiểm tra lại quyền, hiện vật, người mượn và lịch trong giao dịch. Hợp lệ → **Chờ bàn giao**, lưu người duyệt, hạn nhận và giờ dự phòng, bắt đầu giữ lịch. Tài sản chuyển **Chờ bàn giao** và ẩn khỏi Khám phá. Các phiếu còn Chờ duyệt của cùng tài sản tự **Từ chối**, lưu người/thời điểm xử lý với đúng lý do **Đã có người khác mượn tài sản này**. Quy tắc áp dụng cho mọi phiếu chờ của tài sản đó; chỉ có một phiếu đã duyệt/đang mượn. Duyệt đồng thời vẫn chỉ có một phiếu thắng. Không tự xét duyệt phiếu của mình.

Nếu không chấp nhận → Từ chối → ghi lý do trong popup → Từ chối. Phiếu không giữ lịch. Nếu kiểm tra thất bại, phiếu vẫn Chờ duyệt và trả thông báo; thành viên có thể hủy rồi đặt lại, quản lý có thể từ chối với lý do phù hợp.

## 7. Hủy phiếu trước bàn giao

Người mượn hoặc quản lý đơn vị sở hữu → mở phiếu Chờ duyệt/Chờ bàn giao → Hủy phiếu → nhập lý do → xác nhận.

Kết quả: **Đã hủy**, không còn giữ lịch; tài sản đủ điều kiện chia sẻ xuất hiện lại trên Khám phá. Các phiếu tự từ chối trước đó giữ nguyên kết quả; biên bản chưa hoàn tất bị hủy và mất các xác nhận đang có. Không hủy phiếu đã hoàn tất bàn giao; hiện vật đã giao phải đi qua quy trình trả. Phiếu hủy được giữ lại để tra cứu.

## 8. Hết hạn nhận

Phiếu Chờ bàn giao → đến hạn nhận mà chưa hoàn tất giao → tác vụ máy chủ kiểm tra định kỳ 30 giây → **Hết hạn nhận** → bỏ hiệu lực giữ lịch và hủy biên bản chưa hoàn tất. Tài sản còn đủ điều kiện chia sẻ sẽ hiển thị lại; phiếu đã từ chối không tự mở lại.

Hạn nhận tính từ lúc bắt đầu mượn theo chính sách và không vượt quá thời gian kết thúc. Bàn giao cũng kiểm tra giờ nhận trực tiếp, nên không thể giao quá hạn trong lúc chờ tác vụ chạy. Không tự áp dụng Hết hạn nhận cho phiếu Chờ duyệt hoặc phiếu Đang mượn.

## 9. Bàn giao tài sản

1. Đến thời gian nhận, quản lý mở phiếu Chờ bàn giao trong Xử lý mượn–trả.
2. Hai bên kiểm tra hiện vật và phụ kiện tại địa điểm giao nhận.
3. Quản lý chọn **Bàn giao tài sản**, nhập nội dung, tình trạng Đạt và ảnh/chứng từ nếu có → **Xác nhận bàn giao**. Hệ thống lưu biên bản và xác nhận bên giao trong cùng lần gửi.
4. Đúng người mượn mở phiếu, đọc nội dung/phiên bản → **Đã nhận tài sản**. Không có hộp xác nhận thứ hai.
5. Đủ hai tài khoản độc lập cùng phiên bản → biên bản Hoàn tất, phiếu **Đang mượn**, tài sản **Đã được mượn** (ẩn khỏi Khám phá), lưu giờ giao và người giữ. Chỉ quản lý ký thì phiếu vẫn Chờ bàn giao, tài sản Chờ bàn giao.

Chưa tới giờ, đã hết hạn, tài sản Bảo trì/Chờ thu hồi, còn người khác giữ hoặc chưa hết dự phòng thì không giao. Không bàn giao hiện vật hư hỏng và không xác nhận thay người còn lại.

## 10. Sửa, hủy hoặc mở lại biên bản

Quản lý được sửa biên bản giao/nhận trả chưa hoàn tất; người mượn được sửa nội dung trả của mình. **Chỉnh sửa biên bản → sửa → Lưu & xác nhận**: nội dung/đối tác thay đổi sẽ tăng phiên bản, bỏ cả hai xác nhận cũ và ghi xác nhận của người đang sửa. Bên còn lại phải đọc và xác nhận lại phiên bản mới. Gửi xác nhận phiên bản cũ bị từ chối.

Lưu đúng nội dung và cùng đối tác, cùng phiên bản hiện tại không làm mất xác nhận bên kia. Hủy biên bản tăng phiên bản và xóa xác nhận, không hủy phiếu; Mở lại biên bản yêu cầu xác nhận lại khi phiếu còn hợp lệ. Biên bản Hoàn tất được giữ nguyên.

## 11. Hoàn trả và đóng phiếu

1. Đúng người mượn mở phiếu Đang mượn → **Trả tài sản** → ghi tình trạng Đạt/Hư hỏng, nội dung/phụ kiện, ảnh nếu có → **Xác nhận trả tài sản**.
2. Hệ thống đồng thời chuyển phiếu Chờ xác nhận trả, lưu biên bản và xác nhận bên giao (người mượn). Bên nhận mặc định là quản lý đã giao còn hoạt động; nếu không còn phù hợp thì chọn quản lý hoạt động khác của đơn vị sở hữu. Khi có nhiều quản lý, người mượn có thể chọn người nhận trả trong form.
3. Quản lý nhận trả mở phiếu, kiểm tra thực tế và nội dung → **Xác nhận đã nhận trả**. Nếu cần chỉnh sửa, chọn Chỉnh sửa biên bản rồi Lưu & xác nhận; người mượn phải xác nhận lại nội dung mới.
4. Đủ hai xác nhận → biên bản Hoàn tất, phiếu **Đã hoàn trả**, lưu giờ trả thực tế. Trước đó trách nhiệm giữ vẫn còn.
5. Trả Đạt: hết phiếu đang mượn thì tài sản trở lại Đang chia sẻ và hiện trên Khám phá, vẫn giữ giờ dự phòng; nếu trước đó đã được ghi nhận cần Bảo trì thì không tự mở lại chia sẻ; nếu Chờ thu hồi thì hoàn tất thu hồi và ẩn hồ sơ.
6. Trả Hư hỏng: vẫn đóng phiếu, đồng thời chuyển Bảo trì, cập nhật tình trạng và ghi sự cố trong cùng giao dịch.

Không có bước thanh toán, thu tiền hoặc kế toán trong luồng này.

## 12. Quá hạn trả

Phiếu Đang mượn/Chờ xác nhận trả → qua giờ kết thúc mà chưa nhận trả xong → hiện nhãn **Quá hạn trả**. Hệ thống không tự đóng phiếu hay cho rằng hiện vật đã được trả, và chặn yêu cầu/lịch mới khi vẫn có người giữ quá hạn.

Người mượn vẫn báo trả, quản lý kiểm tra và hai bên xác nhận như mục 11. Hoàn tất trả mới đóng trách nhiệm; dự phòng tính từ giờ trả thực tế.

## 13. Trạng thái tài sản và thu hồi

Không dùng Tạm ngừng hoặc Ngừng sử dụng. Các trạng thái nghiệp vụ gồm Chờ duyệt, Từ chối, Đang chia sẻ, Chờ bàn giao, Đã được mượn, Bảo trì và Chờ thu hồi. Trạng thái mượn hiển thị được suy ra từ phiếu đang xử lý; Đã thu hồi chỉ hiện trên phiếu lịch sử, hồ sơ đã thu hồi được ẩn.

Muốn lấy lại tài sản và không chia sẻ nữa, dùng duy nhất **Thu hồi tài sản** theo mục 2. Khi đang mượn, yêu cầu thu hồi không hủy phiếu đã giao hoặc bỏ qua xác nhận trả.

## 14. Báo sự cố, xử lý và đánh giá vòng đời

Người đang giữ → chi tiết phiếu → Báo sự cố → mô tả → Gửi sự cố. Lịch sử ghi hiện trạng; tài sản được đánh dấu cần Bảo trì, vẫn giữ trách nhiệm trả của người mượn. Nếu đã Chờ thu hồi, báo sự cố không thay đổi yêu cầu thu hồi.

Quản lý chỉ được mở **Xử lý & đánh giá vòng đời** khi không còn người giữ và tài sản không Chờ thu hồi. Form ghi nội dung kiểm tra, tình trạng và một trong hai quyết định:

- Tiếp tục chia sẻ: kiểm tra đạt, danh mục/người phụ trách còn hoạt động → Đang chia sẻ.
- Bảo trì: cần sửa chữa → Bảo trì, không nhận mượn mới hoặc bàn giao.

Phải giải quyết các phiếu chưa giao bị ảnh hưởng hoặc chọn hủy trong cùng form. Trả hỏng tự chuyển Bảo trì; nhận trả trong luồng thu hồi thì hoàn tất thu hồi, không tự chia sẻ lại. Không có quyết định Ngừng sử dụng trong form.

## 15. Nhu cầu sử dụng tự xuất hiện sau hoàn trả

Không có nút thêm hoặc sửa nhu cầu riêng. Khi đặt mượn, hệ thống lưu phương án ban đầu **Mua mới** hoặc **Hoãn nhu cầu sử dụng** cùng phiếu, để không khai báo ngược sau khi biết kết quả. Hồ sơ này chưa xuất hiện trong tab Nhu cầu sử dụng hoặc hàng chờ xác minh.

Sau khi hai bên hoàn tất biên bản Trả và phiếu chuyển Đã hoàn trả, nhu cầu tự xuất hiện trong danh sách của người mượn và quản lý đơn vị mượn. Chờ duyệt, từ chối, hủy, hết hạn nhận hoặc mới chỉ một bên ký trả đều chưa đủ điều kiện. Các đường dẫn thêm/sửa/gửi nhu cầu riêng đã bị loại khỏi API.

## 16. Khai báo kết quả mua mới

Sau khi hoàn trả hoàn tất, người lập mở phiếu có liên kết nhu cầu → mục Nhu cầu & kết quả sử dụng → chọn Có mua mới/Không mua mới/Chưa xác định → **Lưu kết quả** ngay trên phiếu. Cũng có thể khai báo trong hồ sơ nhu cầu tự xuất hiện sau hoàn trả.

Nếu chưa rõ kết quả, chọn Chưa xác định. Hồ sơ vẫn có trong danh sách sau hoàn trả và chỉ xác minh được khi người lập đã khai báo Có hoặc Không mua mới. Sửa kết quả đã xác minh đưa hồ sơ về Chờ xác minh.

## 17. Xác minh kết quả nhu cầu

Quản lý **đơn vị có nhu cầu** → Hiệu quả sử dụng → tab Xác minh nhu cầu → mở hồ sơ sau hoàn trả → xem phương án ban đầu, kết quả mua và phiếu/biên bản liên kết → Xác minh kết quả → xác nhận dự định mua mới ban đầu, mượn có đáp ứng mục đích hay không → nhập kết luận đối chiếu → xác nhận.

Chấp nhận → **Đã xác minh**. Không chấp nhận → **Từ chối**. Quản lý tự đánh dấu mức đáp ứng sau khi đối chiếu. Giao diện khóa lựa chọn dự định mua mới nếu phương án ban đầu là Hoãn nhu cầu sử dụng. Người lập không được tự xác minh; nhu cầu do quản lý lập cần quản lý khác cùng đơn vị đối chiếu. Mỗi nhu cầu chỉ có một bản xác minh hiện hành.

## 18. Tính chỉ số và xuất kết quả

Quản lý đơn vị có nhu cầu → Hiệu quả sử dụng → tab Chỉ số tránh mua mới → chọn Từ ngày, Đến trước ngày, loại tài sản. Kết quả tự tải theo bộ lọc hợp lệ, không cần bấm Xem kết quả.

- **D:** Nhu cầu khác nhau của đơn vị có lượt mượn đã hoàn trả, đã khai báo kết quả mua mới, được xác minh có dự định mua và có thời điểm kết thúc dự kiến trong kỳ theo giờ Việt Nam.
- **A:** Phần trong D đã có phiếu đóng, được xác nhận đáp ứng mục đích và người lập xác nhận Không mua mới.
- **R = A/D × 100%**. D = 0 thì không tính tỷ lệ.

Chỉ số chỉ phản ánh các lượt đã mượn–trả, không đại diện cho toàn bộ nhu cầu công ty. Mỗi nhu cầu tính một lần, kể cả có nhiều phiếu liên kết. Trang hiển thị từng nhu cầu, đạt/chưa đạt và lý do. Chọn Xuất CSV để tải danh sách đối chiếu. Không tính theo số lần mượn, trọng số hoặc số tiền tiết kiệm; giả định được ghi ngay trên trang.

## 19. Quản trị tài khoản

Mỗi mục quản trị có ô tìm kiếm tự lọc sau khoảng 300 ms, hỗ trợ chữ hoa/thường và tiếng Việt không dấu. Dropdown áp dụng ngay, kết hợp với từ khóa; Xóa bộ lọc khôi phục danh sách. Đổi mục sẽ xóa bộ lọc cũ.

Tài khoản lọc theo đơn vị, vai trò và Hoạt động/Đã khóa; tìm theo họ tên hoặc tên đăng nhập. Danh sách vẫn không hiển thị email.

Quản trị → Quản trị hệ thống → Tài khoản → Tạo tài khoản → nhập tên, đăng nhập, email, đơn vị, mật khẩu và vai trò → lưu. Tài khoản bắt đầu sử dụng theo quyền và đơn vị được cấp.

Sửa tài khoản: chọn biểu tượng sửa → đổi thông tin/quyền/mật khẩu/trạng thái → lưu → các phiên cũ bị thu hồi. Trước khi khóa/đổi đơn vị/bỏ quyền, hệ thống chặn tài khoản còn trách nhiệm trên phiếu, biên bản, tài sản hoạt động hoặc nhu cầu đang xử lý. Không tự khóa, tự bỏ quản trị hoặc loại bỏ quản trị hoạt động cuối cùng. Không có tự đăng ký tài khoản ngoài hệ thống.

## 20. Quản trị đơn vị, địa điểm, loại tài sản

Đơn vị tìm theo tên/địa chỉ, Loại tài sản tìm theo tên, Địa điểm tìm theo tên/đơn vị/mô tả. Cả ba mục lọc theo trạng thái; Địa điểm có thêm dropdown đơn vị.

Quản trị → tab Đơn vị → Thêm đơn vị → nhập tên, **địa chỉ cụ thể**, trạng thái → lưu. Sửa tương tự; địa chỉ hiện trong hồ sơ tài sản và thông tin đơn vị của người dùng.

Tab Địa điểm → thêm tên, đơn vị, mô tả, trạng thái → lưu. Địa điểm đã có tài sản không chuyển sang đơn vị khác. Tab Loại tài sản → thêm/sửa tên và trạng thái → lưu.

Ngừng danh mục đang được dữ liệu hoạt động sử dụng sẽ bị chặn. Chỉ xóa mục chưa được tham chiếu; dữ liệu lịch sử có liên kết được giữ nguyên.

## 21. Quản trị chính sách mượn

Tìm theo tên chính sách và lọc Đang áp dụng/Chưa đến hiệu lực/Đã thay thế. Đang áp dụng là chính sách có thời điểm hiệu lực gần nhất không lớn hơn hiện tại; chính sách cũ vẫn được giữ để đối chiếu phiếu.

Quản trị → Chính sách mượn → Thêm chính sách → nhập tên, số ngày tối đa, giờ chờ nhận, giờ dự phòng và thời điểm hiệu lực → lưu.

Yêu cầu mới dùng chính sách có hiệu lực mới nhất khi gửi phiếu. Chính sách đã gắn với phiếu không được sửa/xóa; muốn thay quy định thì tạo chính sách mới. Phiếu cũ giữ chính sách của nó để kiểm tra và tra cứu thống nhất.

## 22. Tệp đính kèm, đổi mật khẩu, đăng xuất

**Tệp:** Trong biểu mẫu → Đính kèm tệp → chọn ảnh PNG/JPG/WEBP hoặc PDF, tối đa 8 MB → tải xong → lưu biểu mẫu. Ảnh tài sản không nhận PDF. Ảnh vừa chọn hiện xem trước ngay. Xem ảnh/chứng từ mở popup trong trang; đóng popup quay lại form đang nhập. PDF hiển thị trong khung xem cùng nguồn. Mở tệp được kiểm tra quyền; chọn Bỏ tệp chỉ bỏ liên kết trong biểu mẫu, không xóa dữ liệu nghiệp vụ. Ảnh minh họa sản phẩm không tự thành chứng từ giao nhận.

**Đổi mật khẩu:** Menu tài khoản → Đổi mật khẩu → nhập mật khẩu hiện tại và mật khẩu mới từ 8 ký tự → xác nhận → các phiên cũ hết hiệu lực → đăng nhập lại.

**Đăng xuất:** Menu tài khoản → Đăng xuất → thu hồi phiên → về màn hình đăng nhập. Dữ liệu đã lưu không mất. Phiên hết hạn hoặc khởi động lại máy chủ cũng yêu cầu đăng nhập lại.

## Cách đồng bộ và giới hạn thao tác

Thay đổi được ghi ngay trong SQL. Danh sách/chi tiết tự tải lại khi chuyển về cửa sổ và định kỳ 30 giây; có thể dùng Làm mới hoặc tải lại trang để xem ngay. Đây là đồng bộ theo yêu cầu HTTP, chưa dùng WebSocket.

Phiếu đã hủy/từ chối/hết hạn hoặc đã đóng được lưu lịch sử. Riêng Thu hồi tài sản sẽ xóa các phiếu còn Chờ duyệt/Chờ bàn giao cùng biên bản chưa hoàn tất. Không sửa biên bản hoàn tất hoặc mở lại hồ sơ đã thu hồi. Các chức năng tài chính, kế toán, mua sắm, mượn nhiều hiện vật trong một phiếu, mượn ngoài tổ chức và IoT nằm ngoài phạm vi hiện tại.

Tìm kiếm trong danh sách tài sản, phiếu mượn và nhu cầu đều cập nhật theo nội dung đang nhập; đổi từ khóa/bộ lọc đưa về trang 1. Phản hồi tìm kiếm cũ đến chậm không ghi đè kết quả mới.

Trạng thái mượn hiển thị của tài sản được tính từ phiếu hiện hành (Chờ bàn giao/Đã được mượn); trạng thái vòng đời vẫn được giữ để không mở lại tài sản đang Bảo trì hoặc Chờ thu hồi chỉ vì hủy/đóng phiếu.

## Tên trạng thái dùng thống nhất

- Phiếu mượn: Chờ duyệt → Chờ bàn giao → Đang mượn → Chờ xác nhận trả → Đã hoàn trả. Các kết thúc khác: Từ chối, Đã hủy, Hết hạn nhận.
- Tài sản: Chờ duyệt/Từ chối trước khi chia sẻ; Đang chia sẻ → Chờ bàn giao → Đã được mượn. Bảo trì dùng cho sửa chữa. Thu hồi ẩn ngay nếu chưa giao, hoặc Chờ thu hồi rồi ẩn sau hoàn trả.
- Biên bản: Chưa xác nhận (chưa bên nào ký) → Chờ xác nhận (đã có một bên) → Hoàn tất (đủ hai bên cùng phiên bản); Đã hủy khi bị hủy/mở lại theo quy định.
- Nhu cầu: Bản nháp chỉ dành hồ sơ cũ chưa gửi; Chờ xác minh → Đã xác minh hoặc Từ chối. Thay đổi kết quả đã xác minh sẽ về Chờ xác minh.

Cột `PhieuMuon.TrangThai` lưu mã theo nhãn hiển thị: Chờ duyệt (`CHO_DUYET`), Chờ bàn giao (`CHO_BAN_GIAO`), Đang mượn (`DANG_MUON`), Chờ xác nhận trả (`CHO_XAC_NHAN_TRA`), Đã hoàn trả (`DA_HOAN_TRA`), Từ chối (`TU_CHOI`), Đã hủy (`DA_HUY`) và Hết hạn nhận (`HET_HAN_NHAN`). Cảnh báo Quá hạn trả được tính riêng và hiển thị cùng bước đang xử lý.

Hủy/từ chối/hết hạn vẫn giữ những bước đã đi qua trên thanh tiến độ. Tài sản chỉ mở lại sau khi phiếu thực sự chuyển sang Hết hạn nhận qua tác vụ máy chủ (mỗi 30 giây), đồng nhất với trạng thái phiếu; không bàn giao khi đã qua hạn.

Form nhu cầu và xác minh đã bỏ đính kèm căn cứ, Xem căn cứ nhu cầu và Xem căn cứ xác minh. Đánh giá vòng đời đã bỏ trường căn cứ đánh giá, vẫn yêu cầu quyết định và tình trạng sau kiểm tra khi mở lại tài sản. Chỉ số phản ánh khai báo và kết quả đối chiếu, không giả định có chứng từ dự định mua.
