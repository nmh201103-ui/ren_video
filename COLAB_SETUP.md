# 🆓 Google Colab SadTalker Setup - MIỄN PHÍ 100%

## ✅ Colab HOÀN TOÀN FREE!

- **GPU:** Tesla T4 (16GB VRAM) - Miễn phí
- **Không giới hạn:** Số lượng video
- **Giới hạn:** 12 giờ/session (sau đó restart)
- **Không cần:** Cài đặt gì trên máy
- **Không cần:** GPU laptop

---

## 🚀 Setup 3 Bước (5 phút)

### Bước 1: Upload Notebook

1. Mở: https://colab.research.google.com
2. **File** → **Upload notebook**
3. Chọn file: `SadTalker_Colab_Free.ipynb` (trong project)
4. **Runtime** → **Change runtime type** → **GPU (T4)** → **Save**

### Bước 2: Chạy Setup (1 lần duy nhất)

Chạy **Cell 1** (cài đặt SadTalker):
- Mất 5-10 phút
- Chỉ chạy 1 lần khi mở notebook mới
- Có thể có warning → bỏ qua

### Bước 3: Khởi động API Server

Chạy **Cell 5** (API Server):
```python
# Cell sẽ hiển thị URL như:
🌐 API URL: https://abc-12-34-567-89.ngrok.io

📋 Copy URL này!
```

**Copy URL** và làm 1 trong 2 cách:

**Cách A: Set environment variable (Khuyến nghị)**
```powershell
# Windows PowerShell
$env:COLAB_API_URL="https://abc-12-34-567-89.ngrok.io"
```

**Cách B: Paste vào GUI**
- Trong GUI, phần AI Avatar sẽ có ô nhập URL
- Paste URL vào đó

---

## 🎬 Sử dụng

### Trong Python GUI:

1. **✅ Tick:** "🤖 Sử dụng AI Avatar"
2. **🔘 Chọn:** "🆓 Colab (Miễn phí - cần setup)"
3. **Upload ảnh người** (nếu dùng Demo mode)
4. **Tạo video** như bình thường

### Flow:

```
Project → Upload ảnh + audio → Colab API (GPU render) → Download video → Ghép vào timeline
```

**Thời gian:** 30-60 giây/scene (render trên GPU cloud)

---

## 📝 Workflow Manual (Không dùng API)

Nếu không muốn setup API, có thể dùng manual:

### 1. Tạo video trên Colab:

1. Chạy **Cell 2** → Upload ảnh + audio
2. Chạy **Cell 3** → Đợi render (30-60s)
3. Chạy **Cell 4** → Download video về

### 2. Import vào project:

1. Copy video vào folder `assets/temp/`
2. Đổi tên: `avatar_scene_0.mp4`, `avatar_scene_1.mp4`...
3. Project sẽ tự động dùng video này

---

## ⚙️ Troubleshooting

### Lỗi "No GPU available"
```
Runtime → Change runtime type → GPU (T4) → Save
Restart runtime: Runtime → Restart runtime
```

### Lỗi "ngrok URL expired"
- URL chỉ tồn tại khi session chạy
- Session timeout sau 12h idle
- Chạy lại Cell 5 để lấy URL mới

### Lỗi "API connection failed"
```powershell
# Check URL đã set chưa
echo $env:COLAB_API_URL

# Test URL (PowerShell)
Invoke-WebRequest -Uri "$env:COLAB_API_URL/health"
```

### Session bị disconnect
- Colab free có giới hạn thời gian
- Mở tab Colab, click vào notebook để giữ session sống
- Hoặc cài extension "Colab alive"

---

## 💡 Tips

### Tối ưu chi phí (100% free):

1. **Chỉ render 1 scene avatar:**
   Sửa code `render.py` line ~115:
   ```python
   # Chỉ scene đầu dùng AI avatar, còn lại ảnh tĩnh
   if self.use_ai_avatar and scene_idx == 0 and self.person_image_path:
       avatar_video = self._create_avatar_scene(...)
   ```

2. **Batch processing:**
   - Upload nhiều ảnh + audio vào Colab
   - Render tất cả cùng lúc
   - Download về rồi import vào project

3. **Reuse avatar:**
   - Dùng 1 avatar cho nhiều video
   - Chỉ thay đổi audio

---

## 🆚 So sánh Colab vs D-ID

| Feature | Colab (FREE) | D-ID (PAID) |
|---------|--------------|-------------|
| **Giá** | 🆓 Miễn phí | 💳 $5.9/tháng |
| **GPU cần** | ❌ Không | ❌ Không |
| **Setup** | ⚙️ 5 phút | ✅ 30 giây |
| **Số video** | ♾️ Unlimited | 50/tháng |
| **Chất lượng** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Tốc độ** | 🐢 30-60s | 🚀 20-40s |
| **Internet** | ✅ Cần | ✅ Cần |
| **Session limit** | ⏰ 12h | ♾️ Không |

**Kết luận:** Colab tốt nhất cho bạn (laptop yếu + cần miễn phí)!

---

## 📹 Video hướng dẫn

Xem chi tiết setup:
- YouTube: "SadTalker on Google Colab Tutorial"
- Hoặc: https://github.com/OpenTalker/SadTalker#colab

---

## 🔗 Resources

- Colab Notebook: `SadTalker_Colab_Free.ipynb`
- SadTalker GitHub: https://github.com/OpenTalker/SadTalker
- Google Colab: https://colab.research.google.com
- Ngrok Docs: https://ngrok.com/docs

---

**Enjoy FREE AI Avatar! 🎉**
