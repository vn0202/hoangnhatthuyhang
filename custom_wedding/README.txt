HƯỚNG DẪN THAY ĐỔI ẢNH & THÔNG TIN THIỆP CƯỚI
=====================================================

1. THAY ĐỔI THÔNG TIN CHỮ (info.json):
   Mở file "info.json" bằng bất kỳ trình soạn thảo nào và cập nhật:
   - Tên chú rể, cô dâu (tên đầy đủ, tên ngắn, tên bố mẹ).
   - Ngày dương lịch, ngày âm lịch, thứ, giờ tổ chức (cho cả Nhà Trai và Nhà Gái).
   - Địa điểm tổ chức, địa chỉ chi tiết.
   - Thông tin tài khoản ngân hàng mừng cưới:
     * "ten_ngan_hang": Tên ngân hàng (ví dụ: "Techcombank", "MB Bank", "Vietcombank", ...)
     * "so_tai_khoan": Số tài khoản (ví dụ: "190356789...", ...)
     * "chu_tai_khoan": Tên chủ tài khoản (ví dụ: "TRAN HOANG NHAT")
   - Nút "MỪNG CƯỚI":
     * Mặc định nếu để trống ("") số tài khoản / ngân hàng, nút "MỪNG CƯỚI" sẽ TỰ ĐỘNG ẨN đi.
     * Có thể chủ động tắt nút bằng cách đặt: "hien_nut_mung_cuoi": false ở đầu file info.json.

2. THAY ĐỔI HÌNH ẢNH:
   - "hero.jpg" (tùy chọn): Đặt ảnh bìa lớn mở đầu thiệp cưới vào thư mục này.
   - "savedate.jpg" hoặc "couple.jpg" (tùy chọn): Ảnh cặp đôi phần "QUYẾT ĐỊNH BÊN NHAU TRỌN ĐỜI / Save the date".
   - "groom.jpg" hoặc "chure.jpg" (tùy chọn): Đặt ảnh chân dung chú rể vào thư mục này.
   - "bride.jpg" hoặc "codau.jpg" (tùy chọn): Đặt ảnh chân dung cô dâu vào thư mục này.
   - "timeline.jpg" (tùy chọn): Ảnh mục lịch trình / Timeline.
   - "qr_groom.jpg" / "qr_nhatrai.jpg" (tùy chọn): Ảnh mã QR ngân hàng chú rể.
   - "qr_bride.jpg" / "qr_nhagai.jpg" (tùy chọn): Ảnh mã QR ngân hàng cô dâu.
   - "album/": Thả toàn bộ các ảnh cưới khác của bạn vào thư mục "album/".
     (Bao nhiêu ảnh cũng được: 5 ảnh, 10 ảnh hay 20 ảnh. Hệ thống sẽ tự động phân bổ thông minh vào toàn bộ các khung ảnh album kỷ niệm trên thiệp cưới, thay thế 100% không còn sót ảnh cặp đôi cũ).

3. ÁP DỤNG THAY ĐỔI:
   Chạy lệnh sau tại thư mục gốc của project:
   python3 apply_wedding.py

4. NẾU MUỐN QUAY LẠI MẪU GỐC BAN ĐẦU:
   python3 apply_wedding.py --reset
