# 🎬 Affiliate Video Creator

Ứng dụng Python để tự động tạo video affiliate từ link sản phẩm trên Shopee và TikTok Shop.

## ✨ Tính năng

- ✅ GUI đơn giản, dễ sử dụng
- ✅ Tự động phát hiện platform (Shopee/TikTok Shop)
- ✅ Lấy thông tin sản phẩm tự động (title, price, images)
- ✅ Tự động xử lý và tạo video với text và ảnh
- ✅ Hỗ trợ format video vertical (1080x1920) phù hợp TikTok/Shorts
- ✅ Xuất file MP4 chất lượng cao

## 📁 Cấu trúc dự án

```
affiliate_video_creator/
│
├── main.py                # Entry point
├── requirements.txt
│
├── gui/
│   ├── __init__.py
│   ├── app.py             # Tkinter UI
│   └── widgets.py         # Custom widgets
│
├── scraper/
│   ├── __init__.py
│   ├── base.py            # Interface chung
│   ├── shopee.py          # Lấy data Shopee
│   └── tiktok.py          # Lấy data TikTok Shop
│
├── processor/
│   ├── __init__.py
│   └── content.py         # Làm sạch text, CTA
│
├── video/
│   ├── __init__.py
│   ├── render.py          # MoviePy render
│   └── templates.py       # Template video
│
├── assets/
│   ├── fonts/
│   ├── music/
│   └── images/
│
├── output/
│   └── videos/            # Video output sẽ được lưu ở đây
│
└── utils/
    ├── __init__.py
    ├── downloader.py      # Download images
    └── helpers.py         # Helper functions
```

## 🚀 Cài đặt

1. **Clone hoặc tải project về**

2. **Cài đặt Python dependencies:**
```bash
pip install -r requirements.txt
```

**Lưu ý:** 
- MoviePy cần ffmpeg. Nếu chưa có, cài đặt từ [ffmpeg.org](https://ffmpeg.org/download.html)
- Trên Windows, có thể dùng: `choco install ffmpeg` hoặc tải installer từ website

3. **Chạy ứng dụng:**
```bash
python main.py
```

## 💻 Sử dụng

1. Mở ứng dụng bằng lệnh `python main.py`
2. Nhập link sản phẩm từ Shopee hoặc TikTok Shop vào ô input
3. Click nút "Tạo Video"
4. Chờ quá trình xử lý:
   - Phát hiện platform
   - Lấy thông tin sản phẩm
   - Xử lý nội dung
   - Tạo video
5. Video sẽ được lưu trong thư mục `output/videos/`

## 🔄 Luồng xử lý

```
GUI (app.py)
   ↓
Nhận link sản phẩm
   ↓
Phát hiện nền tảng (Shopee / TikTok)
   ↓
Scraper lấy:
   - title
   - price
   - image_urls
   ↓
Processor:
   - cắt title
   - tạo CTA
   ↓
Video Renderer:
   - chọn template
   - ghép ảnh + text
   ↓
Xuất video mp4
```

## 📝 Ví dụ

### Input:
```
https://shopee.vn/product/123456/789012
```

### Output:
- Video MP4 với:
  - Title sản phẩm
  - Hình ảnh sản phẩm
  - Giá sản phẩm
  - CTA: "Mua ngay trên Shopee!"

## ⚙️ Tùy chỉnh

### Thay đổi template video

Chỉnh sửa file `video/templates.py` để thay đổi:
- Kích thước video
- Màu sắc
- Font size
- Thời lượng các phần tử

### Thêm platform mới

1. Tạo file scraper mới trong `scraper/` (ví dụ: `lazada.py`)
2. Implement class kế thừa `BaseScraper`
3. Thêm vào `utils/helpers.py` để detect platform mới

## 🐛 Xử lý lỗi

- **Lỗi "Cannot find ffmpeg":** Cài đặt ffmpeg và đảm bảo nó có trong PATH
- **Lỗi "Cannot scrape product":** Kiểm tra lại link, có thể website đã thay đổi cấu trúc
- **Lỗi download images:** Kiểm tra kết nối internet

## 📄 License

MIT License

## 🤝 Đóng góp

Mọi đóng góp đều được chào đón! Vui lòng tạo issue hoặc pull request.




