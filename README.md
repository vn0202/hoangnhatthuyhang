# Thiệp Cưới Online: Hoàng Nhật & Thúy Hằng

Website thiệp cưới online cao cấp dành riêng cho cặp đôi **Trần Hoàng Nhật & Vũ Thúy Hằng**, hỗ trợ tách biệt thông tin hiển thị và link chia sẻ Zalo / Facebook cho cả **Nhà Trai (Lễ Thành Hôn)** và **Nhà Gái (Lễ Vu Quy)**.

---

## 1. Khởi động xem trước (Localhost)

Mở Terminal tại thư mục này và chạy:
```bash
python3 -m http.server 8000
```
Sau đó truy cập:
- **Trang chủ (Tự nhận diện bên hoặc mặc định Nhà Trai):** `http://localhost:8000/`
- **Thiệp Nhà Trai (Lễ Thành Hôn):** `http://localhost:8000/nhatrai/` (hoặc `http://localhost:8000/nhatrai.html`)
- **Thiệp Nhà Gái (Lễ Vu Quy):** `http://localhost:8000/nhagai/` (hoặc `http://localhost:8000/nhagai.html`)
- **Hoặc dùng link tham số:** `http://localhost:8000/?side=nhagai` / `http://localhost:8000/?side=nhatrai`

---

## 2. Hướng dẫn cập nhật thông tin & hình ảnh

Toàn bộ thông tin tùy biến nằm gọn trong thư mục `custom_wedding/`:

### A. Thay đổi thông tin chữ (`custom_wedding/info.json`):
- Tên cô dâu, chú rể, tên phụ huynh.
- Ngày dương lịch, ngày âm lịch, thứ, giờ tổ chức riêng cho từng bên.
- Địa điểm và địa chỉ chi tiết (hệ thống tự động đồng bộ link Google Maps chỉ đường).
- Thông tin số tài khoản / ngân hàng mừng cưới.

### B. Thay đổi hình ảnh (`custom_wedding/`):
- `hero.jpg`: Ảnh bìa lớn mở đầu thiệp cưới.
- `savedate.jpg` (hoặc `couple.jpg`): Ảnh cặp đôi phần "QUYẾT ĐỊNH BÊN NHAU TRỌN ĐỜI / Save the date".
- `groom.jpg` (hoặc `chure.jpg`): Ảnh chân dung chú rể.
- `bride.jpg` (hoặc `codau.jpg`): Ảnh chân dung cô dâu.
- `timeline.jpg`: Ảnh lịch trình timeline.
- `qr_groom.jpg` / `qr_bride.jpg`: Ảnh mã QR ngân hàng.
- `album/`: Thả toàn bộ các ảnh cưới khác vào đây để tự động phân bổ vào album kỷ niệm ("Our memories").

---

## 3. Xuất bản / Áp dụng thay đổi

Sau khi chỉnh sửa `info.json` hoặc thêm bớt ảnh, chỉ cần chạy lệnh:
```bash
python3 apply_wedding.py
```
*(Nếu muốn khôi phục về giao diện gốc: `python3 apply_wedding.py --reset`)*
