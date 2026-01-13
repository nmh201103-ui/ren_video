# 🤖 AI Avatar Integration Guide

## Tính năng Talking Avatar với D-ID API

Project hiện hỗ trợ tạo **video người nói chuyển động** từ ảnh tĩnh + giọng đọc sử dụng D-ID API.

---

## 🚀 Cách sử dụng

### 1. Đăng ký D-ID API Key

1. Truy cập: https://studio.d-id.com/
2. Đăng ký tài khoản (Free trial: 20 credits = ~20 videos)
3. Vào **Settings** → **API Key** → Copy key

### 2. Cấu hình API Key

**Windows:**
```powershell
# PowerShell
$env:DID_API_KEY="your-api-key-here"

# Hoặc set vĩnh viễn
[System.Environment]::SetEnvironmentVariable('DID_API_KEY', 'your-key', 'User')
```

**Linux/Mac:**
```bash
export DID_API_KEY="your-api-key-here"

# Hoặc thêm vào ~/.bashrc hoặc ~/.zshrc
echo 'export DID_API_KEY="your-key"' >> ~/.bashrc
```

**Hoặc tạo file `.env` trong project:**
```
DID_API_KEY=your-api-key-here
```

### 3. Chạy app

```bash
# Kích hoạt venv
.\.venv\Scripts\Activate.ps1

# Chạy GUI
python main.py
```

### 4. Tạo video với AI Avatar

1. **Chọn mode "Video Demo"** hoặc "Video Đơn Giản"
2. **Tick checkbox**: ✅ "🤖 Sử dụng AI Avatar (Talking Head - D-ID)"
3. **Upload ảnh người** (JPG/PNG) - ảnh chân dung rõ mặt
4. **Nhập URL sản phẩm** và click "Tạo Video"

---

## 📊 So sánh các chế độ

| Chế độ | Ảnh | Giọng đọc | Chuyển động |
|--------|-----|-----------|-------------|
| **Simple** | Sản phẩm tĩnh | ✅ | ❌ |
| **Demo** | Người cầm SP tĩnh | ✅ | ❌ |
| **Simple + AI Avatar** | Người nói + SP | ✅ | ✅ Môi, đầu |
| **Demo + AI Avatar** | Người nói cầm SP | ✅ | ✅ Môi, đầu |

---

## ⚙️ Quy trình kỹ thuật

### Flow tạo AI Avatar:

```
1. User upload ảnh người
2. TTS tạo audio từ script
3. D-ID API:
   - Upload ảnh → get image_url
   - Upload audio → get audio_url
   - POST /talks → tạo talking video
   - Poll status → đợi hoàn thành (30-120s)
   - Download video kết quả
4. Ghép video avatar vào timeline
5. Export video cuối cùng
```

### Code structure:

```
video/
├── did_avatar.py       # D-ID API integration
└── render.py           # Video renderer (đã tích hợp avatar)

gui/
└── app.py              # GUI với checkbox AI Avatar

requirements.txt        # Dependencies (không cần thêm gì)
```

---

## 💡 Tips & Best Practices

### ✅ Ảnh người tốt nhất:
- **Chân dung rõ mặt** (không bị che)
- **Nhìn thẳng** vào camera
- **Ánh sáng tốt** (không quá tối/sáng)
- **Kích thước**: 512x512px trở lên
- **Format**: JPG hoặc PNG

### ⚠️ Lưu ý:
- Mỗi video tiêu tốn **1 credit**
- Free tier: **20 credits**
- Mỗi scene render riêng → nhiều scenes = nhiều credits
- Thời gian render: **30-120 giây/scene**
- Cần **internet ổn định**

### 🔧 Troubleshooting:

**Lỗi "API key missing":**
```bash
# Check xem đã set chưa
echo $env:DID_API_KEY  # Windows PowerShell
echo $DID_API_KEY      # Linux/Mac
```

**Lỗi "Upload failed":**
- Kiểm tra ảnh không quá lớn (< 10MB)
- Kiểm tra audio format (MP3/WAV)

**Lỗi "Timeout":**
- Tăng `max_wait` trong code (mặc định 120s)
- Kiểm tra internet connection

---

## 📈 Nâng cấp

### Giảm chi phí:
- Chỉ dùng AI Avatar cho scene đầu (hook)
- Các scene sau dùng ảnh tĩnh
- Sửa code `render.py` line ~115:
  ```python
  # Chỉ dùng AI Avatar cho scene 0
  if self.use_ai_avatar and scene_idx == 0 and self.person_image_path and audio_path:
      ...
  ```

### Nâng cấp lên paid plan:
- **Creator**: $5.9/month → 50 credits
- **Pro**: $29/month → 300 credits
- **Advanced**: $196/month → unlimited

---

## 🎥 Demo

**Input:**
- Ảnh: `reviewer_face.jpg` (1 người nhìn thẳng)
- Audio: TTS từ script review
- Sản phẩm: Áo khoác Shopee

**Output:**
- Video 20s: Người nói review + ảnh sản phẩm
- Miệng cử động theo giọng nói
- Đầu nhẹ nhàng chuyển động

---

## 🔗 Resources

- D-ID Documentation: https://docs.d-id.com/
- API Reference: https://docs.d-id.com/reference/basic
- Pricing: https://www.d-id.com/pricing/
- Support: support@d-id.com

---

## 📝 Changelog

**v2.0 (2026-01-11)**
- ✅ Tích hợp D-ID API
- ✅ GUI checkbox AI Avatar
- ✅ Auto fallback nếu API fail
- ✅ Multi-scene support

---

Made with ❤️ for affiliate marketers 🚀
